# Remove Pickle Deserialization in MABI Voice Interface

## Summary
The MABI voice interface script currently uses Python's `pickle` module to load a pre-trained Support Vector Machine (SVM) model. This proposal suggests replacing the `pickle` serialization format with a secure alternative, such as ONNX, to eliminate remote code execution vulnerabilities.

## Problem
In `scripts/mabi_voice_interface.py`, the function `carregar_classificador_svm()` uses `pickle.load(f)` to deserialize the model file `btvox_model_student_svm.pkl`. The `pickle` module is inherently insecure because it can execute arbitrary Python code during the deserialization process. If a malicious actor were to replace or tamper with the `.pkl` file in the `models/` directory, they could achieve remote code execution (RCE) on the host machine.

## Evidence
In `scripts/mabi_voice_interface.py`:
- `import pickle` is on line 20.
- The `carregar_classificador_svm()` function contains the unsafe operation:
  ```python
  with open(MODELO_PKL_PATH, 'rb') as f:
      pacote = pickle.load(f)
  ```

## Proposed Solution
1. Export the trained SVM model from the original training environment (e.g., the PROJETO_MABI notebook) into the ONNX (Open Neural Network Exchange) format using tools like `skl2onnx` (if it's a scikit-learn model) or another compatible exporter.
2. Update `scripts/mabi_voice_interface.py` to use ONNX Runtime (`onnxruntime` package) for inference instead of loading a Python object via `pickle`.
3. Remove the `.pkl` file from the repository's `models/` directory and replace it with the `.onnx` version.
4. Update `requirements.txt` to include `onnxruntime` and remove any dependencies strictly tied to the pickled pipeline (if they are no longer needed).

## Benefits
- **Security:** Completely mitigates the RCE risk associated with `pickle` deserialization.
- **Interoperability:** ONNX is a language-agnostic standard, making it easier to deploy the model in other environments (e.g., C++, Rust) in the future.
- **Performance:** ONNX Runtime is highly optimized and may offer inference speedups compared to a standard Python object pipeline.

## Trade-offs
- Requires modifications to the original model training notebook to support exporting to ONNX.
- Adds `onnxruntime` (and potentially `skl2onnx` in the training environment) to the project dependencies.

## Risks
- The specific SVM pipeline (including any custom pre-processing steps embedded in the pickled pipeline) might not have a direct 1:1 mapping in ONNX format without some refactoring of the training code.

## Estimated Complexity
- Medium

## Priority
- High (due to security implications)

## Success Criteria
- `scripts/mabi_voice_interface.py` no longer imports or uses the `pickle` module.
- The model is loaded and inference is performed using ONNX Runtime.
- The voice interface maintains its current classification accuracy.

## Open Questions
- Does the pickled pipeline contain custom Python functions or classes that are not supported by standard ONNX converters like `skl2onnx`? If so, we may need to split the pipeline into standard components or manually implement the custom logic in Python.
