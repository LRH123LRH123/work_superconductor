#!/bin/bash
#SBATCH --job-name=test
#SBATCH --partition=iq-main
#SBATCH --account=def-maiagv
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=1G
#SBATCH --time=00:05:00
#SBATCH --output=asr-%j.out
#SBATCH --error=asr-%j.err
set -euo pipefail
module load StdEnv/2023 gcc/12.3 openmpi/4.1.5 quantumespresso/7.5
export OMP_NUM_THREADS=1
cd "${SLURM_SUBMIT_DIR:?}"
printf 'JobID=%s\nWorkDir=%s\n' "$SLURM_JOB_ID" "$PWD"
dynmat.x -in dynmat.in > asr.output
grep -q 'JOB DONE' asr.output
printf 'GAMMA_ASR_POSTPROCESS_OK\n'
