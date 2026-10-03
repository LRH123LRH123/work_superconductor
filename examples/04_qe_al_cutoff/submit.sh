#!/bin/bash
#SBATCH --job-name=test
#SBATCH --partition=iq-main
#SBATCH --account=def-maiagv
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=00:30:00
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.err
set -euo pipefail
module load StdEnv/2023 gcc/12.3 openmpi/4.1.5 quantumespresso/7.5
export OMP_NUM_THREADS=1
cd "${SLURM_SUBMIT_DIR:?}"
printf 'JobID=%s\nWorkDir=%s\n' "$SLURM_JOB_ID" "$PWD"
module list 2>&1
command -v pw.x
sha256sum /home/runhan/apps/qesssp/Al.pbe-n-kjpaw_psl.1.0.0.UPF
for ecut in 30 40 50 60 80; do
 (
  cd "ecut_${ecut}"
  mkdir -p scratch
  sha256sum scf.in
  mpirun -np "$SLURM_NTASKS" pw.x -in scf.in > output
  grep -q 'convergence has been achieved' output
  grep -q 'JOB DONE' output
  printf 'ECUT_%s_OK\n' "$ecut"
 )
done
printf 'AL_WAVEFUNCTION_CUTOFF_SCAN_OK\n'
