/**
 * Deploy script for AutonomousCentralBank contract.
 *
 * Usage:
 *   genlayer deploy --contract contracts/acb.py
 *
 * This TypeScript file is a reference for the GenLayer JS SDK approach.
 * The genlayer CLI uses the Python contract directly.
 */

import { readFileSync } from "fs";
import { join } from "path";

export default async function main(client: any) {
  const contractPath = join(__dirname, "..", "contracts", "acb.py");
  const contractCode = readFileSync(contractPath, "utf-8");

  console.log("Deploying AutonomousCentralBank...");
  console.log("Contract path:", contractPath);

  const deployTransaction = await client.deployContract({
    code: contractCode,
    args: [],
  });

  console.log("Deployment successful.");
  console.log("Transaction Hash:", deployTransaction.transactionHash);
  console.log("Contract Address:", deployTransaction.contractAddress);
  console.log(
    "Explorer:",
    `https://explorer-studio.genlayer.com/tx/${deployTransaction.transactionHash}`
  );
}