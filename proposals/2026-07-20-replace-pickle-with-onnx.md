# Replace Insecure Pickle Deserialization with ONNX

## Summary
Migrate the MABI Intent Classifier model deserialization from `pickle` to ONNX to mitigate severe security vulnerabilities associated with loading untrusted pickle files.

## Problem
The `mabi_voice_interface.py` script utilizes the Python `pickle` module (`pickle.load()`) to deserialize the scikit-learn SVM classifier model (`modelo_svm_matchboxnet.pkl`). The `pickle` format is inherently insecure. It allows executing arbitrary code during deserialization if a maliciously crafted pickle file is loaded, leading to critical Remote Code Execution (RCE) vulnerabilities. If an attacker replaces the model file, they can execute commands on the host machine.

## Evidence
In `scripts/mabi_voice_interface.py`, line 20 imports `pickle`, and line 56 executes `pacote = pickle.load(f)`:
```python
    try:
        with open(MODELO_PKL_PATH, 'rb') as f:
            pacote = pickle.load(f)
```
Relying on `pickle` for model loading violates fundamental security best practices, particularly when the model could be modified or supplied by untrusted sources.

## Proposed Solution
1. Convert the existing scikit-learn SVM pipeline to the ONNX (Open Neural Network Exchange) format using `skl2onnx`.
2. Save the converted model as a `.onnx` file in the `models/` directory instead of `.pkl`.
3. Update `scripts/mabi_voice_interface.py` (and any other affected components like `intent_classifier.py` if necessary) to load the ONNX model using `onnxruntime`, replacing the `pickle` import and usage entirely.

## Benefits
- **Security**: ONNX models represent computation graphs without allowing arbitrary code execution, fully eliminating the RCE risk associated with `pickle`.
- **Interoperability**: ONNX is widely supported across different languages and runtimes, facilitating easier deployments.
- **Performance**: `onnxruntime` can provide inference optimizations.

## Trade-offs
- Requires a one-time effort to train/convert the existing SVM models to ONNX.
- Requires adding `onnxruntime` and potentially `skl2onnx` (for model conversion scripts) to the project dependencies.

## Risks
- Minor differences in inference behavior or precision between scikit-learn and the ONNX runtime could occur, though typically negligible for SVM classifiers.
- Need to ensure `onnxruntime` performs adequately on the target low-resource hardware (TV Boxes, Orange Pi), though CPU inference for an SVM in ONNX should be very fast.

## Estimated Complexity
- Medium

## Priority
- High

## Success Criteria
- The `.pkl` model file is replaced with a `.onnx` model file in the repository/deployment.
- `pickle` is completely removed from model loading flows in `scripts/mabi_voice_interface.py`.
- The application successfully loads the ONNX model and correctly classifies intents without regressions.

## Open Questions
- What is the best strategy for updating the model training pipeline/notebooks to output ONNX files instead of pickle?
- Does `onnxruntime` have any compatibility issues with the specific low-resource hardware architectures (e.g., ARM64) currently targeted by the project?
