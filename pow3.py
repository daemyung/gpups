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
def powi3(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = tl.math.pow(x.to(tl.float32), 3).to(x.dtype)
    tl.store(y_block_ptr, y, boundary_check=(0,))


@triton.jit
def powf3(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = tl.math.pow(x, 3.0).to(x.dtype)
    tl.store(y_block_ptr, y, boundary_check=(0,))


@triton.jit
def fast_pow3(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = tl.math.fast_powf(x.to(tl.float32), 3.0).to(x.dtype)
    tl.store(y_block_ptr, y, boundary_check=(0,))


@triton.jit
def pow3(
    y_ptr: tl.tensor,
    x_ptr: tl.tensor,
    x_size: tl.int32,
    block_size: tl.constexpr,
):
    y_block_ptr = tl.make_block_ptr(
        y_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )
    x_block_ptr = tl.make_block_ptr(
        x_ptr,
        shape=(x_size,),
        strides=(1,),
        offsets=(0,),
        block_shape=(block_size,),
        order=(0,),
    )

    x = tl.load(x_block_ptr, boundary_check=(0,))
    y = x * x * x
    tl.store(y_block_ptr, y, boundary_check=(0,))


def dispatch(kernel: triton.jit, y: torch.Tensor, x: torch.Tensor):
    kernel[(1,)](y, x, x.numel(), triton.next_power_of_2(x.numel()))


def verify_result():
    factory_kwargs = {"device": "cuda", "dtype": torch.float32}
    x = torch.rand(10, **factory_kwargs)
    y = torch.rand(10, **factory_kwargs)
    z = x * x * x
    dispatch(powi3, y, x)
    torch.allclose(z, y)
    dispatch(powf3, y, x)
    torch.allclose(z, y)
    dispatch(fast_pow3, y, x)
    torch.allclose(z, y)
    dispatch(pow3, y, x)
    torch.allclose(z, y)


@triton.testing.perf_report(
    [
        triton.testing.Benchmark(
            x_names=["x_size"],
            x_vals=[256 * i for i in range(1, 31, 1)],
            line_arg="backend",
            line_vals=["torch", "powi3", "powf3", "fast_powf3", "pow3"],
            line_names=["torch", "powi3", "powf3", "fast_powf3", "pow3"],
            ylabel="milliseconds",
            plot_name="pow3",
            args={"dtype": torch.float32},
        )
    ]
)
def benchmark(x_size, dtype, backend):
    factory_kwargs = {"device": "cuda", "dtype": torch.float32}
    x = torch.rand(x_size, **factory_kwargs)
    y = torch.empty_like(x)

    if backend == "torch":
        return triton.testing.do_bench_cudagraph(lambda: x * x * x)
    elif backend == "powi3":
        return triton.testing.do_bench_cudagraph(lambda: dispatch(powi3, y, x))
    elif backend == "powf3":
        return triton.testing.do_bench_cudagraph(lambda: dispatch(powf3, y, x))
    elif backend == "fast_powf3":
        return triton.testing.do_bench_cudagraph(lambda: dispatch(fast_pow3, y, x))
    else:
        return triton.testing.do_bench_cudagraph(lambda: dispatch(pow3, y, x))


def main():
    torch.cuda.set_stream(torch.cuda.Stream())
    verify_result()
    benchmark.run(show_plots=True, print_data=True)


if __name__ == "__main__":
    main()
