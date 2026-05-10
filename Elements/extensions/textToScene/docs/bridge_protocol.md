# Bridge Protocol

The textToScene system includes three independent processes — the Elements scene, the controller, and the supervisor — through a set of JSON files in a shared directory on the desktop.

```
~/Desktop/scene_bridge/
```

No network sockets or shared memory are used. Each file has a defined owner that writes it and one or more readers that use it. The polling interval is set to 0.5 seconds.

---

## File reference

### `scene_ir.json`

**Purpose:** Authoritative scene state. Represents the committed, user-approved version of the scene.

**Writer:** controller (`mock_ai_contoller.py`) when apply, undo, load and new scene.

**Readers:** controller (loads on start and after undo), code generator (when regenerating the official script), supervisor (indirectly for scene_state).

**Format:** Scene IR tree: root node with `node_type: "scene"`, recursive `children` of `mesh_object` and `group` nodes.
Updated only when the user applies a change. Never modified during a pending request or preview. if the user rejects the change it must not change. 

---

### `preview_scene_ir.json`

**Purpose:** Temporary scene state set by the controller for a pending command. Shows what the scene would look like if the command is applied.

**Writer:** controller — written after a `apply_action_to_ir` call.

**Readers:** controller (reads on apply to promote to official); supervisor (detects the preview is ready and launches the preview scene).

**Format:** Same schema as `scene_ir.json`.

It is created when `status` changes to `preview_ready`. Deleted on apply or reject. If a new request arrives before the user responds, the previous preview file is overwritten.

---

### `ai_request.json`

**Purpose:** The scene writes a request here and the controller reads it, processes it, and updates the `status`.

**Writer:** Elements scene (initial write with `status: "pending"`); controller (updates `status` and adds the result fields).

**Readers:** controller (polls for `status == "pending"`); Elements scene (polls for status changes to update the UI).

**Format:**

```json
{
  "request_id": "req_001",
  "status": "pending",
  "prompt": "add a red cube"
}
```

**Status values:**

| Value | Set by | Meaning |
| `"pending"` | Scene | New request waiting for the controller |
| `"preview_ready"` | Controller | Preview IR and script are available |
| `"applied"` | Controller | Change committed to official scene |
| `"rejected"` | Controller | Preview discarded, scene unchanged |
| `"error"` | Controller | Processing failed; `error` field contains the reason |
| `"new_scene_created"` | Controller | Scene reset to default |
| `"saved"` | Controller | Scene saved to disk |
| `"load_failed"` | Controller | Named scene file not found |

The scene writes a new `ai_request.json` for each command. The controller must finish processing any active request before picking up a new one ( `status != "pending"`).

---

### `ui_state.json`

**Purpose:** The scene writes the user's apply/reject/undo choice here and the controller reads it in the next poll.

**Writer:** Elements scene (writes `action: "apply"`, `"reject"`, or `"undo"`).

**Readers:** controller (`handle_ui_actions` reads this every poll cycle).

**Format:**

```json
{
  "action": "apply",
  "request_id": "req_001"
}
```

**Action values:**

| Value | Effect |
|---|---|
| `"apply"` | Promote preview IR to official; delete preview files; regenerate official script |
| `"reject"` | Delete preview files; leave official scene unchanged |
| `"undo"` | Pop undo stack; reinstate previous scene IR as official |
| `"idle"` | No pending user action (set by controller after processing) |

---

### `scene_state.json`

**Purpose:** Tells the supervisor which script the scene process should currently be running.

**Writer:** Controller — sets `mode` to `"official"` or `"preview"` after each state transition.

**Readers:** Supervisor (`supervisor.py`) — watches for `mode` changes and restarts the scene process with the appropriate script.

**Format:**

```json
{
  "mode": "preview",
  "script": "/path/to/preview_scene.py",
  "request_id": "req_001",
  "updated_at": 1715000000.0
}
```

**Mode values:**

| Value | Active script |
|---|---|
| `"official"` | `Desktop/scene_out.py` |
| `"preview"` | `Desktop/scene_bridge/preview_scene.py` |

---

### `history/undo_stack.json`

**Purpose:** Stack with undo history. Each entry is a complete snapshot of `scene_ir.json` at the point before a change was applied.

**Writer:** THe controller pushes the current official IR onto the stack before promoting a new preview to official.

**Readers:** Controller pops the top of the stack in case of undo.
The top of the stack (last element) is the most recent previous state. On `new_scene` the stack is cleared.
---

### `cache/action_cache.json`

**Purpose:** Persistent cache of LLM responses keyed by normalised prompt text. It is used to avoid API calls for  commands that are exacpty the same with previous across sessions.

**Readers:** The controller calls the llm parser and checks  before every LLM call. If the prompt is not already there, it proceeds with the api call.

**Format:**

```json
{
  "version": 1,
  "updated_at": 1715000000.0,
  "entries": {
    "add red cube": {
      "prompt": "add a red cube",
      "normalized_prompt": "add red cube",
      "action": { "action": "add_object", "object_type": "cube", "color": "red" },
      "updated_at": 1715000000.0
    }
  }
}
```

Only `add_object`, `generate_pattern`, and `generate_composite` actions without scene-dependent fields (object ids, positions) can be added. Movement, deletion, and recolor actions are never cached because they have been used for a specific scene, so it is not valid to be used accross different scenes.

---

## Write / read matrix

| File | Scene | Controller | Supervisor |
|---|---|---|---|
| `scene_ir.json` | — | W (apply/undo/load/new) | — |
| `preview_scene_ir.json` | — | W (preview) / D (apply,reject) | R |
| `ai_request.json` | W (request) | W (status update) | — |
| `ui_state.json` | W (decision) | W (idle reset) | — |
| `scene_state.json` | — | W | R |
| `history/undo_stack.json` | — | W/R | — |
| `cache/action_cache.json` | — | W/R | — |

W = writes, R = reads, D = deletes
