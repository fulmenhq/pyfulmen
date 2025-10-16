# MIME Detection Cross-Language Parity Checklist

This checklist tracks behavioral parity between pyfulmen and gofulmen MIME detection implementations.

**Last Updated**: 2025-10-15
**pyfulmen Version**: v0.1.2
**gofulmen Version**: v0.1.1

## Core Detection Parity

| Feature                            | gofulmen | pyfulmen | Status  | Notes                           |
| ---------------------------------- | -------- | -------- | ------- | ------------------------------- |
| `DetectMimeType([]byte)` signature | ✅       | ✅       | ✅ Pass | Full parity                     |
| JSON object detection              | ✅       | ✅       | ✅ Pass | Fixture: valid-json-object.json |
| JSON array detection               | ✅       | ✅       | ✅ Pass | Fixture: valid-json-array.json  |
| XML declaration detection          | ✅       | ✅       | ✅ Pass | Fixture: valid-xml.xml          |
| YAML key:value detection           | ✅       | ✅       | ✅ Pass | Fixture: valid-yaml.yaml        |
| CSV comma detection (2+)           | ✅       | ✅       | ✅ Pass | Fixture: valid-csv.csv          |
| Plain text detection (>80%)        | ✅       | ✅       | ✅ Pass | Fixture: valid-text.txt         |
| Binary/unknown returns nil/None    | ✅       | ✅       | ✅ Pass | Fixture: binary-unknown.bin     |
| Empty input returns nil/None       | ✅       | ✅       | ✅ Pass | No fixture needed               |

## BOM Handling Parity

| Feature                        | gofulmen | pyfulmen | Status  | Notes                            |
| ------------------------------ | -------- | -------- | ------- | -------------------------------- |
| UTF-8 BOM stripped (EF BB BF)  | ✅       | ✅       | ✅ Pass | Fixture: json-with-utf8-bom.json |
| UTF-16 LE BOM stripped (FF FE) | ✅       | ✅       | ✅ Pass | Unit test                        |
| UTF-16 BE BOM stripped (FE FF) | ✅       | ✅       | ✅ Pass | Unit test                        |
| Leading whitespace trimmed     | ✅       | ✅       | ✅ Pass | Unit test                        |

## Streaming Detection Parity

| Feature                                | gofulmen | pyfulmen | Status  | Notes                 |
| -------------------------------------- | -------- | -------- | ------- | --------------------- |
| `DetectMimeTypeFromReader()` signature | ✅       | ✅       | ✅ Pass | Full parity           |
| Reader preservation (MultiReader)      | ✅       | ✅       | ✅ Pass | ChainedReader pattern |
| Default maxBytes=512                   | ✅       | ✅       | ✅ Pass | Unit test             |
| Large file handling                    | ✅       | ✅       | ✅ Pass | Unit test             |
| Empty reader returns nil/None          | ✅       | ✅       | ✅ Pass | Unit test             |

## File Detection Parity

| Feature                              | gofulmen | pyfulmen | Status  | Notes                   |
| ------------------------------------ | -------- | -------- | ------- | ----------------------- |
| `DetectMimeTypeFromFile()` signature | ✅       | ✅       | ✅ Pass | Full parity             |
| Reads first 512 bytes                | ✅       | ✅       | ✅ Pass | Implementation verified |
| Empty file returns nil/None          | ✅       | ✅       | ✅ Pass | Unit test               |
| FileNotFoundError on missing file    | ✅       | ✅       | ✅ Pass | Unit test               |
| Large file handling (10KB+)          | ✅       | ✅       | ✅ Pass | Unit test               |

## Edge Cases Parity

| Case                         | gofulmen | pyfulmen | Status  | Notes                   |
| ---------------------------- | -------- | -------- | ------- | ----------------------- |
| JSON with leading whitespace | ✅       | ✅       | ✅ Pass | Unit test               |
| YAML not confused with JSON  | ✅       | ✅       | ✅ Pass | Unit test               |
| CSV not confused with text   | ✅       | ✅       | ✅ Pass | Unit test               |
| Single comma not CSV         | ✅       | ✅       | ✅ Pass | Unit test (requires 2+) |

## Parity Summary

- **Total Features**: 28
- **Passing**: 28
- **Failing**: 0
- **Parity Score**: 100%

✅ **Full behavioral parity achieved with gofulmen v0.1.1**
