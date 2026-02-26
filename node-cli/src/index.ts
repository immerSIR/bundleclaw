#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { execSync } from "node:child_process";
import { Command } from "commander";
import AdmZip from "adm-zip";

const program = new Command();
const ENC_MAGIC = Buffer.from("BCLAWENC1");

const CORE_WORKSPACE_FILES = [
  "AGENTS.md",
  "SOUL.md",
  "USER.md",
  "TOOLS.md",
  "IDENTITY.md",
  "MEMORY.md",
  "HEARTBEAT.md"
];

function exists(p: string) { return fs.existsSync(p); }
function mkdirp(p: string) { fs.mkdirSync(p, { recursive: true }); }

function copyIfExists(src: string, dst: string) {
  if (!exists(src)) return;
  mkdirp(path.dirname(dst));
  fs.cpSync(src, dst, { recursive: true });
}

function sha256(file: string): string {
  const h = crypto.createHash("sha256");
  h.update(fs.readFileSync(file));
  return `sha256:${h.digest("hex")}`;
}

function encryptBytes(data: Buffer, passphrase: string): Buffer {
  const salt = crypto.randomBytes(16);
  const iv = crypto.randomBytes(12);
  const key = crypto.pbkdf2Sync(passphrase, salt, 200_000, 32, "sha256");
  const cipher = crypto.createCipheriv("aes-256-gcm", key, iv);
  const encrypted = Buffer.concat([cipher.update(data), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([ENC_MAGIC, salt, iv, tag, encrypted]);
}

function decryptBytes(data: Buffer, passphrase: string): Buffer {
  if (!data.subarray(0, ENC_MAGIC.length).equals(ENC_MAGIC)) return data;
  const salt = data.subarray(ENC_MAGIC.length, ENC_MAGIC.length + 16);
  const iv = data.subarray(ENC_MAGIC.length + 16, ENC_MAGIC.length + 28);
  const tag = data.subarray(ENC_MAGIC.length + 28, ENC_MAGIC.length + 44);
  const payload = data.subarray(ENC_MAGIC.length + 44);
  const key = crypto.pbkdf2Sync(passphrase, salt, 200_000, 32, "sha256");
  const decipher = crypto.createDecipheriv("aes-256-gcm", key, iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(payload), decipher.final()]);
}

function bundleBytesForImport(bundlePath: string, passphrase?: string): Buffer {
  const raw = fs.readFileSync(bundlePath);
  const encrypted = raw.subarray(0, ENC_MAGIC.length).equals(ENC_MAGIC);
  if (!encrypted) return raw;
  if (!passphrase) throw new Error("Bundle is encrypted. Use --encrypt-pass <passphrase>");
  return decryptBytes(raw, passphrase);
}

program.name("bundleclaw").description("OpenClaw state migration tool");

program
  .command("export")
  .requiredOption("--source <path>", "OpenClaw home (e.g., ~/.openclaw)")
  .requiredOption("--workspace <path>", "Workspace path")
  .requiredOption("--out <file>", "Output .bcz file")
  .option("--profile <profile>", "full|memory-only|no-credentials", "full")
  .option("--encrypt-pass <passphrase>", "Encrypt output bundle with passphrase")
  .action((opts) => {
    const source = path.resolve(opts.source);
    const workspace = path.resolve(opts.workspace);
    const out = path.resolve(opts.out);

    const tmp = fs.mkdtempSync(path.join(process.cwd(), "bundleclaw-export-"));
    const payload = path.join(tmp, "payload");
    mkdirp(payload);

    const profile = String(opts.profile || "full");
    if (![
      "full",
      "memory-only",
      "no-credentials"
    ].includes(profile)) throw new Error(`Invalid --profile ${profile}. Use full|memory-only|no-credentials`);

    const includeOpenclaw = profile !== "memory-only";
    const includeCredentials = profile === "full";
    const includeIdentity = profile === "full";
    const includeWorkspaceCore = true;
    const includeWorkspaceMemory = true;
    const includeWorkspaceConfig = profile !== "memory-only";

    if (includeOpenclaw) copyIfExists(path.join(source, "openclaw.json"), path.join(payload, "openclaw.json"));
    if (includeCredentials) copyIfExists(path.join(source, "credentials"), path.join(payload, "credentials"));
    if (includeIdentity) copyIfExists(path.join(source, "identity"), path.join(payload, "identity"));

    const wsDst = path.join(payload, "workspace");
    mkdirp(wsDst);
    if (includeWorkspaceCore) for (const f of CORE_WORKSPACE_FILES) copyIfExists(path.join(workspace, f), path.join(wsDst, f));
    if (includeWorkspaceMemory) copyIfExists(path.join(workspace, "memory"), path.join(wsDst, "memory"));
    if (includeWorkspaceConfig) copyIfExists(path.join(workspace, "config"), path.join(wsDst, "config"));

    const checksums: Record<string, string> = {};
    const openclawJson = path.join(payload, "openclaw.json");
    if (exists(openclawJson)) checksums["payload/openclaw.json"] = sha256(openclawJson);

    const manifest = {
      format: "bundleclaw.v1",
      createdAt: new Date().toISOString(),
      encrypted: Boolean(opts.encryptPass),
      source: { openclawHome: source, workspace },
      includes: {
        openclawJson: exists(openclawJson),
        credentials: exists(path.join(payload, "credentials")),
        identity: exists(path.join(payload, "identity")),
        workspaceCore: includeWorkspaceCore,
        workspaceMemory: exists(path.join(wsDst, "memory")),
        workspaceConfig: exists(path.join(wsDst, "config"))
      },
      checksums
    };
    fs.writeFileSync(path.join(tmp, "manifest.json"), JSON.stringify(manifest, null, 2));

    const zip = new AdmZip();
    zip.addLocalFile(path.join(tmp, "manifest.json"));
    zip.addLocalFolder(payload, "payload");
    mkdirp(path.dirname(out));

    if (opts.encryptPass) {
      const zipBytes = zip.toBuffer();
      fs.writeFileSync(out, encryptBytes(zipBytes, String(opts.encryptPass)));
    } else {
      zip.writeZip(out);
    }

    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(`Created ${out}`);
  });

program
  .command("import")
  .requiredOption("--bundle <file>", "Input .bcz file")
  .requiredOption("--target <path>", "Target ~/.openclaw path")
  .option("--encrypt-pass <passphrase>", "Passphrase for encrypted bundles")
  .action((opts) => {
    const bundle = path.resolve(opts.bundle);
    const target = path.resolve(opts.target);
    const tmp = fs.mkdtempSync(path.join(process.cwd(), "bundleclaw-import-"));

    const zipBytes = bundleBytesForImport(bundle, opts.encryptPass ? String(opts.encryptPass) : undefined);
    const zip = new AdmZip(zipBytes);
    zip.extractAllTo(tmp, true);

    const payload = path.join(tmp, "payload");
    const backup = path.join(target, `.bundleclaw-backup-${Date.now()}`);
    if (exists(target)) {
      mkdirp(path.dirname(backup));
      fs.cpSync(target, backup, { recursive: true });
      console.log(`Backup created: ${backup}`);
    }
    mkdirp(target);

    copyIfExists(path.join(payload, "openclaw.json"), path.join(target, "openclaw.json"));
    copyIfExists(path.join(payload, "credentials"), path.join(target, "credentials"));
    copyIfExists(path.join(payload, "identity"), path.join(target, "identity"));
    copyIfExists(path.join(payload, "workspace"), path.join(target, "workspace"));

    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(`Imported into ${target}`);
  });

program
  .command("verify")
  .requiredOption("--target <path>", "Target ~/.openclaw path")
  .action((opts) => {
    const target = path.resolve(opts.target);
    const checks = [
      ["openclaw.json", exists(path.join(target, "openclaw.json"))],
      ["workspace/SOUL.md", exists(path.join(target, "workspace", "SOUL.md"))],
      ["workspace/memory", exists(path.join(target, "workspace", "memory"))]
    ];
    for (const [name, ok] of checks) console.log(`${ok ? "OK" : "MISSING"}  ${name}`);
    const failed = checks.some(([, ok]) => !ok);
    process.exit(failed ? 1 : 0);
  });

program
  .command("transfer")
  .requiredOption("--bundle <file>", "Bundle file to transfer")
  .requiredOption("--to <dest>", "scp destination, e.g. user@host:/tmp/agent-state.bcz")
  .option("--scp-bin <cmd>", "scp binary", "scp")
  .action((opts) => {
    const bundle = path.resolve(opts.bundle);
    const scpBin = String(opts.scpBin || "scp");
    const to = String(opts.to);
    execSync(`${scpBin} ${JSON.stringify(bundle)} ${JSON.stringify(to)}`, { stdio: "inherit", shell: "/bin/bash" });
    console.log("Transfer complete");
  });

program
  .command("bootstrap")
  .requiredOption("--bundle <file>", "Input .bcz file")
  .requiredOption("--target <path>", "Target ~/.openclaw path")
  .option("--encrypt-pass <passphrase>", "Passphrase for encrypted bundles")
  .option("--restart-cmd <cmd>", "Restart command", "openclaw gateway restart")
  .option("--skip-restart", "Skip gateway restart", false)
  .action((opts) => {
    const bundle = path.resolve(String(opts.bundle));
    const target = path.resolve(String(opts.target));
    const pass = opts.encryptPass ? String(opts.encryptPass) : undefined;

    // Reuse import logic inline
    const tmp = fs.mkdtempSync(path.join(process.cwd(), "bundleclaw-bootstrap-"));
    const zipBytes = bundleBytesForImport(bundle, pass);
    const zip = new AdmZip(zipBytes);
    zip.extractAllTo(tmp, true);

    const payload = path.join(tmp, "payload");
    const backup = path.join(target, `.bundleclaw-backup-${Date.now()}`);
    if (exists(target)) {
      mkdirp(path.dirname(backup));
      fs.cpSync(target, backup, { recursive: true });
      console.log(`Backup created: ${backup}`);
    }
    mkdirp(target);
    copyIfExists(path.join(payload, "openclaw.json"), path.join(target, "openclaw.json"));
    copyIfExists(path.join(payload, "credentials"), path.join(target, "credentials"));
    copyIfExists(path.join(payload, "identity"), path.join(target, "identity"));
    copyIfExists(path.join(payload, "workspace"), path.join(target, "workspace"));
    fs.rmSync(tmp, { recursive: true, force: true });
    console.log(`Imported into ${target}`);

    const checks = [
      ["openclaw.json", exists(path.join(target, "openclaw.json"))],
      ["workspace/SOUL.md", exists(path.join(target, "workspace", "SOUL.md"))],
      ["workspace/memory", exists(path.join(target, "workspace", "memory"))]
    ];
    for (const [name, ok] of checks) console.log(`${ok ? "OK" : "MISSING"}  ${name}`);

    if (!opts.skipRestart) {
      try {
        execSync(String(opts.restartCmd), { stdio: "inherit", shell: "/bin/bash" });
      } catch {
        console.log("WARN  restart failed; run manually:", String(opts.restartCmd));
      }
    }

    try {
      execSync("openclaw doctor --non-interactive", { stdio: "inherit", shell: "/bin/bash" });
    } catch {
      console.log("WARN  doctor reported issues (or unavailable); run manually.");
    }
    try {
      execSync("openclaw status", { stdio: "inherit", shell: "/bin/bash" });
    } catch {
      console.log("WARN  status command failed; run manually.");
    }

    console.log("Bootstrap complete.");
  });

program.parse();
