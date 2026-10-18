# P08 第 1 步：MM-Assist real-world 数据集格式记录

- 访问日期：2026-10-05
- 仓库：https://github.com/cuboulder-se-research/move-method-assist
- 仓库 HEAD：`8b0898fbcaf05b6b4596c2c54b3b156d412c77bb`（2026-01-30）
- 数据文件：`replication-package/artifacts/datasets.zip`
  - sha256：`8b2808944db28ba6620f07a71fce38224f32cc100a444bb89573f662e268c3eb`
  - 最后改动它的 commit：`131502c`（2025-07-30）
- 版本证据的完整记录见 `artefact_version.txt`。
- 落地页上的 datasets.zip 下载链接等同于仓库里的这个文件。

## 1. real-world 数据集在哪

| 子集 | 路径（datasets.zip 内） | 格式 | 条数 |
|---|---|---|---|
| 实例方法（MM-Assist 结果 + oracle） | `data/refminer_data/instance-methods/mm-assist-emm/<project>_res.json` | JSON 数组，每个项目一个文件，共 11 个 | 117 |
| 实例方法基线 | `instance-methods/feTruth/*.json`、`instance-methods/jmove/*.txt` | JSON / TSV | — |
| 实例方法 ID 映射 | `instance-methods/ref_id_map.json` | `{RefactoringMiner 描述: ref_id}` | 912（未经筛选的原始挖掘结果） |
| 静态方法 | `static-methods/mm-assist/*.jsonl`、`static-methods/feTruth-*/` | JSONL / JSON+TSV | 83（不在本研究范围内） |

各项目条数：kafka 41，graal 17，ruoyi-vue-pro 11，elasticsearch 9，flink 8，spring-boot 8，dbeaver 5，ghidra 5，selenium 5，redisson 4，spring-framework 4。

## 2. 每条记录的结构（`mm-assist-emm/*_res.json`）

```
{
  "repository": "https://github.com/dbeaver/dbeaver.git",
  "sha1": "8c8725f1...",            # 开发者真实的重构 commit（重构后状态）
  "url": "...",
  "ref_id": 887,                    # 唯一整数 ID，取值 1–905
  "move_method_refactoring": {
    "type": "Extract And Move Method",        # 117 条全部是这个类型
    "description": "Extract And Move Method public createSchemaImpl(...) : OracleSchema extracted from ... in class <HOST_FQN> & moved to class <TARGET_FQN>",
    "leftSideLocations":  [{filePath, startLine, endLine, codeElementType, description, codeElement}, ...],
    "rightSideLocations": [... {"description": "extracted method declaration", "codeElement": "<method signature>"} ...],
    "isStatic": false
  },
  "extraction_results": {
    "success": true,
    "newCommitHash": "67832724...",           # 作者构造的“移动前”状态
    "newBranchName": "extract-<m>-<src>-<parent7>"
  },
  "telemetry": {                              # MM-Assist 运行日志（3 条记录没有这个字段）
    "hostFunctionTelemetryData": {"sourceCode": "<宿主类完整源码>", "filePath", "methodCount", ...},
    "candidatesTelemetryData", "iterationData", "methodCompatibilityScores",
    "llmMethodPriority", "targetClassMap"
  }
}
```

## 3. 标识字段的对应关系

| 需要的字段 | 来源 |
|---|---|
| case ID | `ref_id` |
| 项目名 | `repository` 的最后一段，去掉 `.git` |
| commit hash | 用 `extraction_results.newCommitHash` 作为研究的 checkout 点；`sha1` 只作溯源记录 |
| 宿主类 | `description` 中 `in class X &` 的 X（全限定名，内部类写作 `Outer.Inner`） |
| 宿主类文件路径 | `leftSideLocations[0].filePath`（相对仓库根目录） |
| 方法名 / 签名 | `rightSideLocations` 中 `description == "extracted method declaration"` 那一项的 `codeElement` |
| 目标类（gold） | `description` 中 `moved to class Y` 的 Y（全限定名） |
| 实例 / 静态 | `move_method_refactoring.isStatic`；这个子集里 117 条全部是 `false` |

用正则解析以上字段，117 条全部成功，0 条失败。

## 4. 对第 2–4 步有影响的发现（需要组内决定）

1. **所有案例都是 “Extract And Move Method”，不是纯 Move Method。**
   - 开发者在真实提交里是“先抽取再移动”。论文作者在开发者提交的父 commit 上，先把被抽取的方法放回宿主类，生成 `newCommitHash`，这才得到“移动前”状态。
   - 所以第 2 步的 checkout 点是 `newCommitHash`，不是 `sha1`。
   - 已验证 redisson 的一个案例：作者构造的 commit（作者 Abhiram98，提交说明 “match developer changes”）可以用 `git fetch origin <newCommitHash>` 从 GitHub 上取到，并且包含被抽取的方法。
   - 建议把规则 (2) 写成：`newCommitHash` 可 fetch，且该 commit 中存在宿主文件。
2. **有 3 条记录 `extraction_results.success = false` 且没有 telemetry。**
   - 建议在 D-03 中把“构造成功”列为显式的数据完整性条件。
   - 应用规则 (1) 和这个条件后，剩 114 条 eligible。
3. **`success` 字段有一条存的是字符串 `"true"`。** 脚本里已经统一处理。
4. **`ref_id` 是唯一的。**
   - 因此“case ID → 文件路径 → 时间顺序”这个排序实际只由 `ref_id` 决定，后两个键不会起作用。
   - 数据里也没有提交日期，如果要用，只能从 git 取。
5. **至少有 2 条记录的宿主类是目标类的内部类**（例如 `OracleDataSource.SchemaCache` → `OracleDataSource`）。
   - 外部类既不是字段类型，也不是参数类型。
   - 按现在的编码手册，这种情况会被判为 H2 或得到 NONE。
   - 需要 D 在手册里写明怎么处理。
6. **`telemetry.hostFunctionTelemetryData.sourceCode` 里存有宿主类的完整源码。**
   - 可以用来核对 checkout 出来的文件。
   - 但 prompt 的输入建议统一从 checkout 读取。

## 5. 筛选脚本

`scripts/select_sample.py` 已按上面的字段写好，可以直接运行：

- **干跑**：只应用规则 (1)，不写任何文件。
- **加 `--check-source`**：逐条做规则 (2) 检查，失败的自动顺延，写出 `data/sample_ids.csv` 和 `data/screening_log.csv`。
- 请在 D-03 提交之后再运行带 `--check-source` 的版本。
