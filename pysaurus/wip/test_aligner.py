from pysaurus.wip.aligner import Aligner

def test():
    A = (
        "theano.gpuarray.tests.check_dnn_conv.TestDnnConv2D.test_fwd('time_once', 'float16', 'float16', "
        "'((2, 3, 300, 5), (2, 3, 40, 4), (1, 1), (1, 1), 'half', 'conv', 2.0, 0)) ... "
        "(using CUDNN_CONVOLUTION_FWD_ALGO_IMPLICIT_PRECOMP_GEMM (timed), ws:0, hash:FWD|GPU#0000:06:00.0 "
        "-t -g 1 -dim 2,3,300,5,4500,1500,5,1 -filt 2,3,40,4 -mode conv -pad 20,2 -subsample 1,1 "
        "-dilation 1,1 -hh [unaligned])"
    )
    B = (
        "theano.gpuarray.tests.check_dnn_conv.TestDnnConv2D.test_fwd('time_once', 'float16', 'float16', "
        "((2, 3, 300, 5), (2, 3, 40, 4), (1, 1), (1, 1), 'half', 'conv', 2.0, 0)) ... "
        "(using CUDNN_CONVOLUTION_FWD_ALGO_IMPLICIT_GEMM (timed), ws:0, hash:FWD|GPU#0000:06:00.0 -t -g 1 "
        "-dim 2,3,300,5,4500,1500,5,1 -filt 2,3,40,4 -mode conv -pad 20,2 -subsample 1,1 -dilation 1,1 -hh [unaligned])"
    )
    alignment = Aligner().align(A, B, debug=False)
    print(alignment.to_string(''))
    al = Aligner().align([1, 1, 0, 1], [1, 1, 1, 1, 1, 1, 1, 1, 0, 1])
    print(al.to_string(' '))


if __name__ == '__main__':
    test()