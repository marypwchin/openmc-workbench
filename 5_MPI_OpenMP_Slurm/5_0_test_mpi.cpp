#include <mpi.h>
#include <stdio.h>

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, size;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    printf("MPI rank %d of %d\n", rank, size);

    MPI_Barrier(MPI_COMM_WORLD);
    int sum;
    MPI_Allreduce(&rank, &sum, 1, MPI_INT, MPI_SUM,
              MPI_COMM_WORLD);
    printf("Rank %d: sum = %d\n", rank, sum);
    MPI_Finalize();
    return 0;
}
