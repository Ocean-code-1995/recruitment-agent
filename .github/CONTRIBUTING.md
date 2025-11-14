# Contributing Guidelines

Welcome to the project! 🎉  
We move fast, but we keep code quality and stability in check.

---

## 🏗️ Branching Model

- **main** → Always stable and demo-ready.  
- **dev** → Integration branch.  
- **feature/<name>** → Active development branches.

**Flow:**
1. Branch off `dev` for your work.
2. Open a Pull Request (PR) into `dev`.
3. Once `dev` is stable, it’s merged into `main` via a PR + review.

Example:
main ← dev ← feature/email-agent


---

## ✅ Pull Request Rules

- All merges into `main` or `dev` **require at least one approving review**.
- Keep PRs **small and focused** (<300 lines if possible).
- Use **clear titles** and **short descriptions** (what + why).
- You can **open draft PRs early** for feedback.
- Squash merge when possible to keep history clean.

**Naming Convention:**
- `feat`: add Gmail OAuth flow
- `fix`: handle missing image extraction
- `docs`: update setup instructions


---

## ⚙️ Branch Protection

**main**
- Requires PR review before merging  
- Requires status checks to pass (CI, tests, lint)  
- Must be up-to-date with base before merging  
- No direct commits or force pushes  

**dev**
- Requires PR review before merging  
- No direct commits or force pushes  
- Status checks optional (for fast iteration)

---

## 🚀 Quick Workflow

1. `git checkout dev`
2. `git pull`
3. `git checkout -b feature/my-new-feature`
4. Make your changes.
5. Push & open a PR → base: `dev`
6. Request a review.
7. Merge when approved and tests pass.
8. Once stable, open a PR from `dev → main`.

---

## 🧹 Hygiene

- Delete merged branches.
- Use Conventional Commits for clarity.
- Keep `main` always deployable/demo-ready.
- If you break something, fix it fast 😉

---

## 💬 Reviews

- At least **one reviewer** per PR.
- Anyone can review — small teams move faster.
- Prefer **pair reviews** for big changes.
- Minor changes (docs, comments) can be self-approved if trivial.

---

Thanks for contributing — keep it fast, clean, and collaborative! 🚀

## ⚙️ Branch Protection Setup (GitHub UI summary)

You can set these under
➡️ Settings → Branches → Branch protection rules

| Branch | Require PR review | Require status checks | Up to date before merge | Restrict pushes | Allow force push |
| :----- | :---------------- | :-------------------- | :---------------------- | :-------------- | :--------------- |
| `main` | ✅                 | ✅                     | ✅                       | ✅               | ❌                |
| `dev`  | ✅                 | optional              | ❌                       | ✅               | ❌                |
