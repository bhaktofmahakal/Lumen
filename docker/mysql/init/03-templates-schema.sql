-- LaTeX Templates Schema
-- Requirements: 9.1, 9.2, 9.3, 9.5

-- Templates Table (for built-in and custom templates)
CREATE TABLE IF NOT EXISTS latex_templates (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    template_id VARCHAR(36) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    description TEXT NULL,
    template_type ENUM('article', 'thesis', 'dissertation', 'conference_paper', 'poster', 'presentation', 'custom') NOT NULL,
    content LONGTEXT NOT NULL,
    placeholder_content LONGTEXT NULL,
    is_builtin BOOLEAN DEFAULT FALSE,
    is_public BOOLEAN DEFAULT FALSE,
    user_id BIGINT UNSIGNED NULL,
    project_id BIGINT UNSIGNED NULL,
    
    -- Customization options (stored as JSON)
    customization_options JSON NULL COMMENT 'Available customization options: paper_size, font, citation_style, margins',
    default_settings JSON NULL COMMENT 'Default settings for the template',
    
    -- Metadata
    journal_name VARCHAR(255) NULL COMMENT 'For journal-specific templates',
    conference_name VARCHAR(255) NULL COMMENT 'For conference-specific templates',
    tags JSON NULL COMMENT 'Tags for template categorization',
    
    usage_count INT UNSIGNED DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    
    INDEX idx_template_id (template_id),
    INDEX idx_template_type (template_type),
    INDEX idx_user_id (user_id),
    INDEX idx_project_id (project_id),
    INDEX idx_is_builtin (is_builtin),
    INDEX idx_is_public (is_public)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Document Outlines Table (for generated outlines)
CREATE TABLE IF NOT EXISTS document_outlines (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    outline_id VARCHAR(36) NOT NULL UNIQUE,
    project_id BIGINT UNSIGNED NOT NULL,
    user_id BIGINT UNSIGNED NOT NULL,
    title VARCHAR(255) NOT NULL,
    research_topic TEXT NOT NULL,
    outline_structure JSON NOT NULL COMMENT 'Hierarchical outline structure with sections and subsections',
    source_document_ids JSON NULL COMMENT 'Document IDs used for outline generation',
    latex_content LONGTEXT NULL COMMENT 'Generated LaTeX structure',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    
    INDEX idx_outline_id (outline_id),
    INDEX idx_project_id (project_id),
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert built-in templates
-- Article template
INSERT INTO latex_templates (
    template_id,
    name,
    description,
    template_type,
    content,
    placeholder_content,
    is_builtin,
    is_public,
    customization_options,
    default_settings
) VALUES (
    UUID(),
    'IEEE Article',
    'Standard IEEE article template for journal submissions',
    'article',
    '\\documentclass[journal]{IEEEtran}
\\usepackage{cite}
\\usepackage{amsmath,amssymb,amsfonts}
\\usepackage{algorithmic}
\\usepackage{graphicx}
\\usepackage{textcomp}
\\usepackage{xcolor}

\\begin{document}

\\title{{{TITLE}}}

\\author{\\IEEEauthorblockN{{{AUTHORS}}}
\\IEEEauthorblockA{{{AFFILIATION}}}}

\\maketitle

\\begin{abstract}
{{ABSTRACT}}
\\end{abstract}

\\begin{IEEEkeywords}
{{KEYWORDS}}
\\end{IEEEkeywords}

\\section{Introduction}
{{INTRODUCTION}}

\\section{Related Work}
{{RELATED_WORK}}

\\section{Methodology}
{{METHODOLOGY}}

\\section{Results}
{{RESULTS}}

\\section{Discussion}
{{DISCUSSION}}

\\section{Conclusion}
{{CONCLUSION}}

\\bibliographystyle{IEEEtran}
\\bibliography{references}

\\end{document}',
    'Enter your paper title, authors, abstract, and complete each section with your research content.',
    TRUE,
    TRUE,
    JSON_OBJECT(
        'paper_size', JSON_ARRAY('letter', 'a4'),
        'font_size', JSON_ARRAY('10pt', '11pt', '12pt'),
        'citation_style', JSON_ARRAY('IEEE', 'APA', 'MLA'),
        'columns', JSON_ARRAY('onecolumn', 'twocolumn')
    ),
    JSON_OBJECT(
        'paper_size', 'letter',
        'font_size', '10pt',
        'citation_style', 'IEEE',
        'columns', 'twocolumn'
    )
);

-- Thesis template
INSERT INTO latex_templates (
    template_id,
    name,
    description,
    template_type,
    content,
    placeholder_content,
    is_builtin,
    is_public,
    customization_options,
    default_settings
) VALUES (
    UUID(),
    'PhD Thesis',
    'Comprehensive PhD thesis template with chapters and appendices',
    'thesis',
    '\\documentclass[12pt,oneside]{book}
\\usepackage[utf8]{inputenc}
\\usepackage[T1]{fontenc}
\\usepackage{amsmath,amssymb}
\\usepackage{graphicx}
\\usepackage{hyperref}
\\usepackage{natbib}
\\usepackage{geometry}
\\geometry{margin=1in}

\\title{{{TITLE}}}
\\author{{{AUTHOR}}}
\\date{{{DATE}}}

\\begin{document}

\\maketitle

\\frontmatter

\\chapter*{Abstract}
{{ABSTRACT}}

\\chapter*{Acknowledgments}
{{ACKNOWLEDGMENTS}}

\\tableofcontents
\\listoffigures
\\listoftables

\\mainmatter

\\chapter{Introduction}
{{INTRODUCTION}}

\\chapter{Literature Review}
{{LITERATURE_REVIEW}}

\\chapter{Methodology}
{{METHODOLOGY}}

\\chapter{Results}
{{RESULTS}}

\\chapter{Discussion}
{{DISCUSSION}}

\\chapter{Conclusion}
{{CONCLUSION}}

\\backmatter

\\bibliographystyle{plainnat}
\\bibliography{references}

\\appendix
\\chapter{Supplementary Material}
{{APPENDIX}}

\\end{document}',
    'Complete each chapter with your research content. Add additional chapters as needed.',
    TRUE,
    TRUE,
    JSON_OBJECT(
        'paper_size', JSON_ARRAY('letter', 'a4'),
        'font_size', JSON_ARRAY('10pt', '11pt', '12pt'),
        'citation_style', JSON_ARRAY('plainnat', 'apa', 'chicago'),
        'margins', JSON_ARRAY('1in', '1.5in', '2cm', '2.5cm'),
        'line_spacing', JSON_ARRAY('single', 'onehalf', 'double')
    ),
    JSON_OBJECT(
        'paper_size', 'letter',
        'font_size', '12pt',
        'citation_style', 'plainnat',
        'margins', '1in',
        'line_spacing', 'double'
    )
);

-- Conference paper template
INSERT INTO latex_templates (
    template_id,
    name,
    description,
    template_type,
    content,
    placeholder_content,
    is_builtin,
    is_public,
    customization_options,
    default_settings,
    conference_name
) VALUES (
    UUID(),
    'ACM Conference Paper',
    'ACM conference paper template (SIGCONF)',
    'conference_paper',
    '\\documentclass[sigconf]{acmart}

\\usepackage{booktabs}
\\usepackage{graphicx}

\\copyrightyear{2024}
\\acmYear{2024}
\\setcopyright{acmlicensed}

\\begin{document}

\\title{{{TITLE}}}

\\author{{{AUTHOR_NAME}}}
\\affiliation{%
  \\institution{{{INSTITUTION}}}
  \\city{{{CITY}}}
  \\country{{{COUNTRY}}}
}
\\email{{{EMAIL}}}

\\begin{abstract}
{{ABSTRACT}}
\\end{abstract}

\\keywords{{{KEYWORDS}}}

\\maketitle

\\section{Introduction}
{{INTRODUCTION}}

\\section{Related Work}
{{RELATED_WORK}}

\\section{Approach}
{{APPROACH}}

\\section{Evaluation}
{{EVALUATION}}

\\section{Conclusion}
{{CONCLUSION}}

\\bibliographystyle{ACM-Reference-Format}
\\bibliography{references}

\\end{document}',
    'Complete each section following ACM conference guidelines. Ensure your abstract is under 150 words.',
    TRUE,
    TRUE,
    JSON_OBJECT(
        'format', JSON_ARRAY('sigconf', 'sigplan', 'sigchi'),
        'citation_style', JSON_ARRAY('ACM-Reference-Format', 'numeric'),
        'review_mode', JSON_ARRAY('true', 'false')
    ),
    JSON_OBJECT(
        'format', 'sigconf',
        'citation_style', 'ACM-Reference-Format',
        'review_mode', 'false'
    ),
    'ACM'
);

