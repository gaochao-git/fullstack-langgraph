# 文档目录说明

本目录是系统的统一文档管理目录，包含以下子目录：

## 目录结构

```
documents/
├── uploads/     # 用户上传的文件
├── templates/   # Word模板文件
├── generated/   # 系统生成的文档
└── README.md    # 本说明文件
```

## 各目录用途

### uploads/
- 存储用户上传的各类文档文件
- 支持的格式：.pdf, .docx, .txt, .md
- 通过文件上传API保存到此目录

### templates/
- 存储Word文档模板
- 主要模板：`公文写作规范模板.docx`
- 备用模板：`template.docx`
- 导出Word时会使用这些模板的样式

### generated/
- 存储系统生成的Word文档
- 文件名格式：`{uuid}.docx`
- 这些文件不会自动清理，需要手动管理

## 配置说明

在 `.env` 文件中配置：
```
DOCUMENT_DIR=documents
```

## 注意事项

1. 请确保 `templates/` 目录中有模板文件
2. `generated/` 目录中的文件需要定期手动清理
3. 所有子目录会在系统启动时自动创建