#!/bin/bash
# One fixed upstream regression case. No k/cutoff/smearing scan.
#SBATCH --job-name=test
#SBATCH --partition=iq-main
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=02:00:00
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
set -euo pipefail
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
module load StdEnv/2023 gcc/12.3 openmpi/4.1.5 quantumespresso/7.5
cd "$SLURM_SUBMIT_DIR"
date -u +%FT%TZ
module list 2>&1
sha256sum scf.in nscf.in epw.in pb_s.UPF
mpirun -np "$SLURM_NTASKS" pw.x -in scf.in > scf.output
grep -q 'convergence has been achieved' scf.output
grep -q 'JOB DONE.' scf.output
echo SCF_OK
mpirun -np "$SLURM_NTASKS" pw.x -in nscf.in > nscf.output
grep -q 'JOB DONE.' nscf.output
echo NSCF_OK
mpirun -np "$SLURM_NTASKS" epw.x -nk "$SLURM_NTASKS" -in epw.in > output
/home/runhan/anaconda3/bin/python validate_epw.py output pb.a2f.01.300.000
echo PB_FIXED_REGRESSION_OK
date -u +%FT%TZ
