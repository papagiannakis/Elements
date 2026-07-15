# System Architecture

The textToScene system converts natural language commands into live 3D scenes rendered by the Elements framework. The pipeline is layered: each stage has a single responsibility and communicates through well-defined data structures.

---

## Pipeline overview

```
User input (natural language)
        │
        ▼
  ┌─────────────┐
  │  Detection  │  detect_procedural_action()
  │  (pre-LLM)  │  Recognises ring / tree / table / lamp /
  └──────┬──────┘  arbitrary object names without LLM call
         │ no match
         ▼
  ┌─────────────┐
  │  LLM parser │  llm_parser.py
  │  + cache    │  Normalises prompt → looks up action cache →
  └──────┬──────┘  calls OpenAI API → stores result in cache
         │ action dict
         ▼
  ┌─────────────────────┐
  │  Normalisation /    │  normalize_action()
  │  Validation         │  Resolves aliases, canonicalises fields
  └──────────┬──────────┘  validate_action() rejects unknown actions
             │
             ▼
  ┌──────────────────┐
  │  Controller      │  mock_ai_contoller.py
  │  apply_action_   │  Resolves target objects, computes new
  │  to_ir()         │  positions, builds / modifies scene IR
  └──────────┬───────┘
             │ new scene IR
             ▼
  ┌──────────────────┐
  │  Code generator  │  code_generator.py
  │  generate_scene_ │  Converts scene IR → executable Python
  │  script()        │  script for the Elements / OpenGL runtime
  └──────────┬───────┘
             │ preview_scene.py
             ▼
  ┌──────────────────┐
  │  Supervisor      │  supervisor.py
  │                  │  Watches scene_state.json; restarts the
  └──────────────────┘  scene process in official or preview mode
```

---

## Stages in detail

### 1. User input

The running Elements scene embeds an ImGui text field. On submission the scene writes `ai_request.json` with `status: "pending"` to the shared bridge directory and waits for a response.

### 2. Procedural detection (`detect_procedural_action`)

Before going to the cache or LLM  ,each prompt goes throuph a regex check. If the command matches a known pattern (build a tree, a table, a street light) it is handled directly without calling the model at all. This keeps the output consistent for commands that have a fixed structure and do not require anty interpretation.

### 3. LLM parser and action cache (`llm_parser.py`)

For all other prompts the system checks a local JSON cache using the normalised version of the prompt. Normalisation removes any filler words, lowercases everything and strips whitespace so that "add a Red Cube" and "please add a red cube" map to the same cache entry. If nothing is found in cache the system calls the Open AI API with a structured prompt that limits the model to a fixed set of actions. The response is then parsed, validated and saved to the cache so that the next same request does not provoke another Api call. Scene-dependent actions (move, delete, recolor) are never cached.

When the user asks for something more open-ended, like "make a wooden chair", a second API call is made with a different prompt that asks the model to break the object down into a list of 3-8 non-overlapping primitives.

### 4. Normalisation and validation

`normalize_action` resolves field aliases that are produced by different LLM phrasings (e.g. `object_id` -> `id`, `back` -> `backward`). `validate_action` then enforces that the action type is in the allowed set and that required fields are present. The unknown action types raise a `ValueError` which is caught and returned as an error status to the UI.

### 5. Controller (`mock_ai_contoller.py`)

The controller is the main process. It:

- resolves object references (by name, colour, creation order, or recency) using `resolve_target_node_with_group`
- computes new object positions using a grid and slot free search (`find_next_free_world_position`, `find_first_free_in_direction`)
- builds the updated scene IR as a copy (deep copy) of the current official IR so a failed action never corrupts the live scene
- writes the preview IR and preview script to the bridge directory
- handles save, load, undo, new scene and prefab instantiation as special cases

### 6. Scene IR

The scene is represented as a JSON tree. The root node has `node_type: "scene"`. Its children are either `mesh_object` nodes (a single primitive with transform, material, and shape) or `group` nodes (a named collection of mesh objects used for prefabs and composite structures). Every node carries a unique `id`, a `created_order` counter, and a `transform` with position and scale.

```json
{
  "node_type": "scene",
  "name": "root",
  "window": { "width": 1200, "height": 800, "title": "Scene" },
  "children": [
    {
      "node_type": "mesh_object",
      "name": "cube_1",
      "id": "cube_1",
      "shape": "cube",
      "transform": { "position": [0.0, 0.5, 0.0], "scale": [1.0, 1.0, 1.0] },
      "material": { "color": [1.0, 0.0, 0.0], "texture": { "enabled": false } }
    }
  ]
}
```

### 7. Code generation (`code_generator.py`)

`generate_scene_script` takes the scene IR and turns it into a standalone Python script that sets up and runs the Elements/OpenGL environment. For each object in the scene it calls `geometry_factory.build_render_mesh` to get the vertex, index, colour and normal arrays, then emits the corresponding Elements entity setup and shader. The generated script also includes the ImGui control panel and the file-polling loop for the bridge.

### 8. Preview / apply / reject / undo

After generating the preview script the controller sets `ai_request.json` to `status: "preview_ready"`. The supervisor switches the running scene process to the preview script. The user can then:

- **Apply** the preview IR becomes the new official scene IR + the preview files are deleted + the official script is regenerated.
- **Reject** the preview files are deleted + the official scene is unchanged.
- **Undo** the controller pops the previous IR from the undo stack and makes it the official scene.

### 9. Supervisor (`supervisor.py`)

The supervisor runs as a separate process and watches scene_state.json for changes. Whenever the active script switches between the official scene and a preview, it stops the current scene process and starts a new one with the updated script. This keeps the rendering separate from the controller logic and ensures the OpenGL window stays stable throughout the editing session.

---

## Module summary

| Module | Responsibility |
|---|---|
| `mock_ai_contoller.py` | Main controller loop, action dispatch, IR manipulation |
| `llm_parser.py` | Prompt normalisation, cache, OpenAI API calls |
| `code_generator.py` | Scene IR → executable Python script |
| `geometry_factory.py` | Primitive mesh data (vertices, indices, normals) |
| `prefabs.py` | Deterministic multi-part group builders |
| `supervisor.py` | Process watchdog, official ↔ preview switching |
| `config.py` | Shared paths, constants, model name |
