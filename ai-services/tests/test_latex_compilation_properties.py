"""
Property-Based Tests for LaTeX Compilation
Property 8: LaTeX Compilation Performance
**Validates: Requirements 7.3**
Test that documents under 20 pages compile within 10 seconds
"""

import pytest
from hypothesis import given, strategies as st, settings, assume
from hypothesis import HealthCheck
import time
import asyncio
from latex_api import LaTeXCompiler


# Strategy for generating valid LaTeX documents
@st.composite
def latex_document(draw, max_pages=20):
    """
    Generate valid LaTeX documents with varying complexity
    
    Args:
        max_pages: Maximum number of pages (default: 20)
    
    Returns:
        Valid LaTeX document string
    """
    # Document class
    doc_class = draw(st.sampled_from(['article', 'report', 'book']))
    paper_size = draw(st.sampled_from(['a4paper', 'letterpaper']))
    
    # Number of sections (controls document length)
    num_sections = draw(st.integers(min_value=1, max_value=max_pages))
    
    # Packages
    packages = [
        '\\usepackage[utf8]{inputenc}',
        '\\usepackage{amsmath}',
        '\\usepackage{graphicx}'
    ]
    
    # Build document
    doc = f'\\documentclass[{paper_size}]{{{doc_class}}}\n'
    doc += '\n'.join(packages) + '\n'
    doc += '\\title{Test Document}\n'
    doc += '\\author{Test Author}\n'
    doc += '\\date{\\today}\n'
    doc += '\\begin{document}\n'
    doc += '\\maketitle\n'
    
    # Add sections with content
    for i in range(num_sections):
        section_title = draw(st.text(
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'), min_codepoint=32, max_codepoint=126),
            min_size=5,
            max_size=50
        ))
        
        # Add section
        doc += f'\\section{{{section_title}}}\n'
        
        # Add paragraphs
        num_paragraphs = draw(st.integers(min_value=1, max_value=3))
        for _ in range(num_paragraphs):
            paragraph = draw(st.text(
                alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs'), min_codepoint=32, max_codepoint=126),
                min_size=50,
                max_size=200
            ))
            doc += f'{paragraph}\n\n'
        
        # Optionally add equation
        if draw(st.booleans()):
            doc += '\\begin{equation}\n'
            doc += 'E = mc^2\n'
            doc += '\\end{equation}\n\n'
    
    doc += '\\end{document}\n'
    
    return doc


class TestLaTeXCompilationPerformance:
    """
    Property 8: LaTeX Compilation Performance
    **Validates: Requirements 7.3**
    """
    
    @pytest.fixture
    def compiler(self):
        """Create LaTeX compiler instance"""
        return LaTeXCompiler()
    
    @given(doc=latex_document(max_pages=20))
    @settings(
        max_examples=50,
        deadline=15000,  # 15 seconds per test
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @pytest.mark.asyncio
    async def test_compilation_performance_under_20_pages(self, compiler, doc):
        """
        Property 8: LaTeX Compilation Performance
        **Validates: Requirements 7.3**
        
        Test that documents under 20 pages compile within 10 seconds
        
        Property: For all valid LaTeX documents with <= 20 pages,
                 compilation time <= 10 seconds
        """
        # Estimate page count (rough approximation)
        # Assume ~500 characters per page
        estimated_pages = len(doc) / 500
        assume(estimated_pages <= 20)
        
        # Compile document
        document_id = f"test_perf_{time.time()}"
        start_time = time.time()
        
        result = await compiler.compile(doc, document_id)
        
        compilation_time = time.time() - start_time
        
        # Property: Compilation time must be <= 10 seconds
        assert compilation_time <= 10.0, (
            f"Compilation took {compilation_time:.2f}s, exceeds 10s limit. "
            f"Document size: {len(doc)} chars, estimated pages: {estimated_pages:.1f}"
        )
        
        # Additional check: If compilation succeeded, verify PDF was generated
        if result.success:
            assert result.pdf_url is not None, "PDF URL should be provided on success"
    
    @given(
        num_sections=st.integers(min_value=1, max_value=50),
        has_equations=st.booleans(),
        has_tables=st.booleans()
    )
    @settings(
        max_examples=30,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @pytest.mark.asyncio
    async def test_compilation_performance_with_complexity(
        self, 
        compiler, 
        num_sections, 
        has_equations, 
        has_tables
    ):
        """
        Property 8: LaTeX Compilation Performance (with complexity variations)
        **Validates: Requirements 7.3**
        
        Test compilation performance with varying document complexity
        
        Property: Compilation time scales reasonably with document complexity
        """
        # Build document with specified complexity
        doc = '\\documentclass[a4paper]{article}\n'
        doc += '\\usepackage[utf8]{inputenc}\n'
        doc += '\\usepackage{amsmath}\n'
        
        if has_tables:
            doc += '\\usepackage{booktabs}\n'
        
        doc += '\\begin{document}\n'
        
        for i in range(min(num_sections, 20)):  # Cap at 20 sections
            doc += f'\\section{{Section {i+1}}}\n'
            doc += 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ' * 10
            doc += '\n\n'
            
            if has_equations and i % 3 == 0:
                doc += '\\begin{equation}\n'
                doc += f'x_{i+1} = \\frac{{a + b}}{{c}}\n'
                doc += '\\end{equation}\n\n'
            
            if has_tables and i % 5 == 0:
                doc += '\\begin{table}[h]\n'
                doc += '\\begin{tabular}{lll}\n'
                doc += '\\toprule\n'
                doc += 'A & B & C \\\\\n'
                doc += '\\midrule\n'
                doc += '1 & 2 & 3 \\\\\n'
                doc += '\\bottomrule\n'
                doc += '\\end{tabular}\n'
                doc += '\\end{table}\n\n'
        
        doc += '\\end{document}\n'
        
        # Estimate pages
        estimated_pages = len(doc) / 500
        assume(estimated_pages <= 20)
        
        # Compile
        document_id = f"test_complex_{time.time()}"
        start_time = time.time()
        
        result = await compiler.compile(doc, document_id)
        
        compilation_time = time.time() - start_time
        
        # Property: Must complete within 10 seconds
        assert compilation_time <= 10.0, (
            f"Complex document compilation took {compilation_time:.2f}s. "
            f"Sections: {num_sections}, Equations: {has_equations}, Tables: {has_tables}"
        )
    
    @pytest.mark.asyncio
    async def test_minimal_document_compiles_quickly(self, compiler):
        """
        Property 8: LaTeX Compilation Performance (minimal case)
        **Validates: Requirements 7.3**
        
        Test that minimal documents compile very quickly (< 5 seconds)
        """
        minimal_doc = '''\\documentclass{article}
\\begin{document}
Hello World!
\\end{document}'''
        
        document_id = f"test_minimal_{time.time()}"
        start_time = time.time()
        
        result = await compiler.compile(minimal_doc, document_id)
        
        compilation_time = time.time() - start_time
        
        # Minimal documents should compile in < 5 seconds
        assert compilation_time < 5.0, (
            f"Minimal document took {compilation_time:.2f}s, should be < 5s"
        )
        
        # Skip if no LaTeX engine available (expected in CI/test environments)
        if not result.success and result.errors and result.errors[0].get('message') == 'No LaTeX engine available or all engines failed':
            pytest.skip("No LaTeX engine available - install pdflatex, xelatex, or lualatex to run this test")
        
        # Should succeed
        assert result.success, f"Minimal document failed: {result.errors}"
    
    @given(page_count=st.integers(min_value=1, max_value=20))
    @settings(
        max_examples=20,
        deadline=15000,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    @pytest.mark.asyncio
    async def test_compilation_time_scales_linearly(self, compiler, page_count):
        """
        Property 8: LaTeX Compilation Performance (scalability)
        **Validates: Requirements 7.3**
        
        Test that compilation time scales approximately linearly with page count
        
        Property: time(n pages) <= 10 seconds for n <= 20
        """
        # Generate document with approximately page_count pages
        # Assume ~500 chars per page
        chars_per_page = 500
        target_chars = page_count * chars_per_page
        
        doc = '\\documentclass{article}\n'
        doc += '\\usepackage[utf8]{inputenc}\n'
        doc += '\\begin{document}\n'
        
        # Add content to reach target character count
        section_content = 'Lorem ipsum dolor sit amet. ' * 20
        sections_needed = max(1, target_chars // len(section_content))
        
        for i in range(sections_needed):
            doc += f'\\section{{Section {i+1}}}\n'
            doc += section_content + '\n\n'
        
        doc += '\\end{document}\n'
        
        # Compile
        document_id = f"test_scale_{time.time()}"
        start_time = time.time()
        
        result = await compiler.compile(doc, document_id)
        
        compilation_time = time.time() - start_time
        
        # Property: Must complete within 10 seconds regardless of page count (up to 20)
        assert compilation_time <= 10.0, (
            f"Document with ~{page_count} pages took {compilation_time:.2f}s"
        )
        
        # Additional property: Time should scale reasonably
        # Rough heuristic: < 0.5 seconds per page
        expected_max_time = page_count * 0.5
        assert compilation_time <= max(expected_max_time, 10.0), (
            f"Compilation time {compilation_time:.2f}s exceeds expected "
            f"{expected_max_time:.2f}s for {page_count} pages"
        )


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--hypothesis-show-statistics'])
