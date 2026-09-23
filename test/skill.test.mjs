import { readFileSync, readdirSync } from "node:fs";
import { strict as assert } from "node:assert";

const skill = readFileSync(new URL("../SKILL.md", import.meta.url), "utf8");
assert.match(skill, /^---\n/, "SKILL.md must start with frontmatter");
assert.match(skill, /name:\s*session-memory-sync/, "frontmatter name");
assert.match(skill, /description:\s*\S/, "frontmatter description");

const scripts = readdirSync(new URL("../scripts", import.meta.url));
for (const f of ["common.py", "sync_push.py", "sync_pull.py"]) {
  assert.ok(scripts.includes(f), `missing scripts/${f}`);
}
console.log("ok");
