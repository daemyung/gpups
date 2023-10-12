# Copyright 2023 ⓒ Daemyung Jang.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import torch
import triton
import triton.language as tl


@triton.jit
def base(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    offset = tl.program_id(0)

    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(offset,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(offset,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = 1 / tl.sqrt(x)
    tl.store(y_block_ptr, y, boundary_check=(0,))


@triton.jit
def sqrt(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    offset = tl.program_id(0)

    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(offset,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(offset,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = 1 / tl.math.sqrt(x)
    tl.store(y_block_ptr, y, boundary_check=(0,))


@triton.jit
def rsqrt(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    offset = tl.program_id(0)

    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(offset,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(offset,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = tl.math.rsqrt(x)
    tl.store(y_block_ptr, y, boundary_check=(0,))


def dispatch(kernel: triton.jit, y: torch.Tensor, x: torch.Tensor):
    def grid(meta):
        return (triton.cdiv(x.numel(), meta["block_size"]),)

    kernel[grid](y, x, x.numel(), 512)


def verify_result():
    factory_kwargs = {"device": "cuda", "dtype": torch.float32}
    x = torch.rand(10, **factory_kwargs)
    y = torch.rand(10, **factory_kwargs)
    z = torch.exp(x)
    dispatch(base, y, x)
    torch.allclose(z, y)
    dispatch(sqrt, y, x)
    torch.allclose(z, y)
    dispatch(rsqrt, y, x)
    torch.allclose(z, y)


@triton.testing.perf_report(
    [
        triton.testing.Benchmark(
            x_names=["x_size"],
            x_vals=[256 * i for i in range(1, 31, 1)],
            line_arg="backend",
            line_vals=["torch", "base", "sqrt", "rsqrt"],
            line_names=["torch", "base", "sqrt", "rsqrt"],
            ylabel="milliseconds",
            plot_name="exp",
            args={"dtype": torch.float32},
        )
    ]
)
def benchmark(x_size, dtype, backend):
    factory_kwargs = {"device": "cuda", "dtype": dtype}
    x = torch.rand(x_size, **factory_kwargs)
    y = torch.empty_like(x)

    if backend == "torch":
        return triton.testing.do_bench_cudagraph(lambda: torch.rsqrt(x))
    elif backend == "base":
        return triton.testing.do_bench_cudagraph(lambda: dispatch(base, y, x))
    elif backend == "sqrt":
        return triton.testing.do_bench_cudagraph(lambda: dispatch(sqrt, y, x))
    else:
        return triton.testing.do_bench_cudagraph(lambda: dispatch(rsqrt, y, x))


def main():
    torch.cuda.set_stream(torch.cuda.Stream())
    verify_result()
    benchmark.run(show_plots=True, print_data=True)


if __name__ == "__main__":
    main()
