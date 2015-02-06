'''
Created on Jul 16, 2014

@author: jeromethai
'''

from networks.wardrop.util import bisection, save_mat
from cvxopt import matrix, spmatrix


def test1():
    def F(x):
        return 1 + 0.15*(x**4)
    print bisection(F, 4.0, 0.0, 5.0)


def test2():
    Ms = [matrix(1.0, (3,2)), spmatrix(1.0, range(3), range(3))]
    names = ['M1', 'M2']
    save_mat(Ms, names, 'test')


def main():
    test1()
    #test2()


if __name__ == '__main__':
    main()