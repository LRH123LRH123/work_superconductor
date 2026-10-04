#!/bin/bash
#SBATCH --job-name=test
#SBATCH --partition=iq-maiagv
#SBATCH --account=def-maiagv
#SBATCH --nodes=1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --mem=8G
#SBATCH --time=01:00:00
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
for case in k08_s020 k12_s020 k16_s020 k20_s020 k08_s010 k12_s010 k16_s010 k20_s010 k08_s005 k12_s005 k16_s005 k20_s005; do
 (
  cd "$case"
  mkdir -p scratch
  sha256sum scf.in
  mpirun -np "$SLURM_NTASKS" pw.x -in scf.in > output
  grep -q 'convergence has been achieved' output
  grep -q 'JOB DONE' output
  printf 'CASE_%s_OK\n' "$case"
 )
done
printf 'AL_KMESH_SMEARING_SCAN_OK\n'
