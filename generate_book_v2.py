#!/usr/bin/env python3
"""
DSET Book Generator V2

Improved markdown to LaTeX conversion for the Dual State Economic Theory book.
Fixes issues with character escaping and formatting.
"""

import os
import re
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class DSETBookGenerator:
    def __init__(self, source_dir: str = "."):
        self.source_dir = Path(source_dir)
        self.output_dir = self.source_dir / "output"
        self.template_file = self.source_dir / "book_template.tex"
        
        # Chapter ordering based on CLAUDE.md structure
        self.chapter_order = [
            ("abstract.md", "Abstract"),
            ("introduction.md", "Introduction"),
            ("chapter_01_foundations.md", "Chapter 1: Foundations of Dual State Economic Theory"),
            ("chapter_02_trust_value_engine.md", "Chapter 2: The Trust-Value Engine"),
            ("chapter_03_lifecycle_of_value.md", "Chapter 3: The Lifecycle of Value"),
            ("chapter_04_flow_mechanics.md", "Chapter 4: Flow Mechanics"),
            ("chapter_05_memory_and_momentum.md", "Chapter 5: Memory and Momentum"),
            ("chapter_06_scarcity_and_abundance.md", "Chapter 6: Scarcity and Abundance"),
            ("chapter_07_narrative_and_meaning.md", "Chapter 7: Narrative and Meaning"),
            ("chapter_08_systems_of_accountability.md", "Chapter 8: Systems of Accountability"),
            ("chapter_09_ritual_and_symbol.md", "Chapter 9: Ritual and Symbol"),
            ("chapter_10_anatomy_of_collapse.md", "Chapter 10: Anatomy of Trust Collapse"),
            ("chapter_11_redemption_dynamics.md", "Chapter 11: Redemption Dynamics"),
            ("chapter_12_systemic_collapse.md", "Chapter 12: Systemic Collapse"),
            ("chapter_13_regenerative_design.md", "Chapter 13: Regenerative Design"),
            ("chapter_14_weight_of_wealth.md", "Chapter 14: The Weight of Wealth"),
            ("chapter_15_collectivism_vs_individualism.md", "Chapter 15: Collectivism vs. Individualism"),
            ("chapter_16_personal_action.md", "Chapter 16: Personal Action"),
            ("chapter_19_theology_of_value.md", "Chapter 19: Theology of Value"),
            ("appendix_01.md", "Appendix A: Mathematical Formalism")
        ]
        
        # Create output directory
        self.output_dir.mkdir(exist_ok=True)
        
    def escape_latex_chars(self, text: str) -> str:
        """Escape special LaTeX characters in plain text only."""
        # Skip if this looks like it already has LaTeX commands
        if '\\textbf{' in text or '\\textit{' in text or '\\section{' in text:
            return text
            
        # Protect placeholders from escaping
        placeholder_pattern = r'<<<PLACEHOLDER_\d+>>>'
        protected_placeholders = {}
        placeholder_counter = 0
        
        for match in re.finditer(placeholder_pattern, text):
            temp_key = f"__TEMP_PLACEHOLDER_{placeholder_counter}__"
            protected_placeholders[temp_key] = match.group(0)
            text = text.replace(match.group(0), temp_key, 1)
            placeholder_counter += 1
            
        # Order matters - handle these characters
        replacements = [
            ("\\", "\\textbackslash{}"),
            ("&", "\\&"),
            ("%", "\\%"), 
            ("$", "\\$"),
            ("#", "\\#"),
            ("_", "\\_"),
            ("{", "\\{"),
            ("}", "\\}"),
            ("^", "\\textasciicircum{}"),
            ("~", "\\textasciitilde{}")
        ]
        
        for old, new in replacements:
            text = text.replace(old, new)
        
        # Restore placeholders
        for temp_key, original_placeholder in protected_placeholders.items():
            text = text.replace(temp_key, original_placeholder)
        
        return text
        
    def process_inline_formatting(self, text: str) -> str:
        """Process inline markdown formatting to LaTeX."""
        # Store original formatting patterns and their LaTeX replacements
        
        # Process bold **text**
        bold_pattern = r'\*\*([^*]+)\*\*'
        def bold_replacement(match):
            content = match.group(1)
            # Don't escape content that's inside formatting - it will be escaped later
            return f"\\textbf{{{content}}}"
        text = re.sub(bold_pattern, bold_replacement, text)
        
        # Process italic *text* (but not bold)
        italic_pattern = r'(?<!\*)\*([^*]+)\*(?!\*)'
        def italic_replacement(match):
            content = match.group(1)
            return f"\\textit{{{content}}}"
        text = re.sub(italic_pattern, italic_replacement, text)
            
        # Process inline code `text`
        code_pattern = r'`([^`]+)`'
        def code_replacement(match):
            content = match.group(1)
            return f"\\texttt{{{content}}}"
        text = re.sub(code_pattern, code_replacement, text)
        
        # Now escape LaTeX special characters, but skip content inside LaTeX commands
        text = self.escape_latex_chars(text)
        
        return text
        
    def convert_markdown_to_latex(self, markdown_content: str, unnumbered_sections: bool = False) -> str:
        """Convert markdown content to LaTeX format.
        
        Args:
            markdown_content: The markdown content to convert
            unnumbered_sections: If True, use unnumbered sections (for Abstract/Introduction)
        """
        lines = markdown_content.split('\n')
        latex_lines = []
        in_code_block = False
        in_itemize = False
        
        for line in lines:
            # Handle code blocks
            if line.strip().startswith('```'):
                if in_code_block:
                    latex_lines.append('\\end{verbatim}')
                    in_code_block = False
                else:
                    latex_lines.append('\\begin{verbatim}')
                    in_code_block = True
                continue
                
            if in_code_block:
                latex_lines.append(line)
                continue
                
            # Skip main title (# Title) - it's handled by the chapter structure
            if line.startswith('# ') and not line.startswith('## '):
                continue
                
            # Handle headers
            if line.startswith('#### '):
                header_text = self.escape_latex_chars(line[5:].strip())
                if unnumbered_sections:
                    latex_lines.append(f"\\paragraph*{{{header_text}}}")
                else:
                    latex_lines.append(f"\\paragraph{{{header_text}}}")
            elif line.startswith('### '):
                header_text = self.escape_latex_chars(line[4:].strip())
                if unnumbered_sections:
                    latex_lines.append(f"\\subsubsection*{{{header_text}}}")
                else:
                    latex_lines.append(f"\\subsubsection{{{header_text}}}")
            elif line.startswith('## '):
                header_text = self.escape_latex_chars(line[3:].strip())
                if unnumbered_sections:
                    latex_lines.append(f"\\section*{{{header_text}}}")
                else:
                    latex_lines.append(f"\\section{{{header_text}}}")
                
            # Handle bullet points
            elif line.strip().startswith('- '):
                if not in_itemize:
                    latex_lines.append('\\begin{itemize}')
                    in_itemize = True
                # Process the bullet content
                bullet_content = self.process_inline_formatting(line.strip()[2:])
                latex_lines.append(f"\\item {bullet_content}")
                
            # Handle numbered lists
            elif re.match(r'^\d+\.\s', line.strip()):
                if in_itemize:
                    latex_lines.append('\\end{itemize}')
                    in_itemize = False
                # Add proper paragraph break for numbered items
                content = self.process_inline_formatting(line.strip())
                latex_lines.append('')  # Add blank line before
                latex_lines.append(content)
                latex_lines.append('')  # Add blank line after
                
            # Handle regular text
            elif line.strip():
                # Close itemize if needed
                if in_itemize:
                    latex_lines.append('\\end{itemize}')
                    in_itemize = False
                    
                # Process inline formatting
                processed_line = self.process_inline_formatting(line)
                latex_lines.append(processed_line)
                
            # Handle empty lines
            else:
                if in_itemize:
                    latex_lines.append('\\end{itemize}')
                    in_itemize = False
                latex_lines.append('')
                
        # Close any remaining environments
        if in_itemize:
            latex_lines.append('\\end{itemize}')
            
        return '\n'.join(latex_lines)
        
    def process_chapter(self, filename: str, title: str) -> Optional[str]:
        """Process a single chapter file."""
        file_path = self.source_dir / filename
        
        if not file_path.exists():
            print(f"Warning: Chapter file {filename} not found, skipping...")
            return None
            
        print(f"Processing: {filename}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Convert to LaTeX - use unnumbered sections for Abstract and Introduction
        unnumbered = filename in ["abstract.md", "introduction.md"]
        latex_content = self.convert_markdown_to_latex(content, unnumbered_sections=unnumbered)
        
        # Handle special cases
        if filename == "abstract.md":
            # For abstract, just return the content
            return latex_content
        elif filename == "introduction.md":
            return latex_content
        elif filename.startswith("appendix"):
            return f"\\appendix\n\\chapter{{{title[11:]}}}\n{latex_content}"
        else:
            # Regular chapters - extract chapter number and title
            # Remove "Chapter X: " prefix and handle the colon properly
            chapter_title = title[10:] if title.startswith("Chapter ") else title
            # If there's a colon at the start (from chapters 10+), remove it
            if chapter_title.startswith(": "):
                chapter_title = chapter_title[2:]
            return f"\\chapter{{{chapter_title}}}\n{latex_content}"
            
    def generate_book(self, output_filename: str = "dset_book.tex") -> bool:
        """Generate the complete book."""
        print("Generating DSET Book (V2)...")
        
        # Read template
        if not self.template_file.exists():
            print(f"Error: Template file {self.template_file} not found!")
            return False
            
        with open(self.template_file, 'r', encoding='utf-8') as f:
            template = f.read()
            
        # Process chapters
        abstract_content = ""
        introduction_content = ""
        chapters_content = []
        
        for filename, title in self.chapter_order:
            content = self.process_chapter(filename, title)
            if content is None:
                continue
                
            if filename == "abstract.md":
                abstract_content = content
            elif filename == "introduction.md":
                introduction_content = content
            else:
                chapters_content.append(content)
                
        # Replace placeholders in template
        book_content = template.replace("% PLACEHOLDER_ABSTRACT", abstract_content)
        book_content = book_content.replace("% PLACEHOLDER_INTRODUCTION", introduction_content)
        book_content = book_content.replace("% PLACEHOLDER_CHAPTERS", '\n\n'.join(chapters_content))
        
        # Write output file
        output_path = self.output_dir / output_filename
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(book_content)
            
        print(f"Book generated: {output_path}")
        return True
        
    def compile_pdf(self, tex_filename: str = "dset_book.tex") -> bool:
        """Compile LaTeX to PDF."""
        tex_path = self.output_dir / tex_filename
        
        if not tex_path.exists():
            print(f"Error: LaTeX file {tex_path} not found!")
            return False
            
        print("Compiling PDF...")
        
        # Change to output directory for compilation
        original_dir = os.getcwd()
        os.chdir(self.output_dir)
        
        try:
            # Run pdflatex twice for proper cross-references
            for i in range(2):
                print(f"Running pdflatex (pass {i+1}/2)...")
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', tex_filename],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'
                )
                
                if result.returncode != 0:
                    # Check if PDF was still created
                    pdf_name = tex_filename.replace('.tex', '.pdf')
                    if not Path(pdf_name).exists():
                        print(f"Error in pdflatex pass {i+1}:")
                        print(result.stdout[-2000:])  # Last 2000 chars
                        return False
                    else:
                        print(f"Warning: pdflatex had errors but PDF was created")
                    
            print("PDF compilation complete!")
            pdf_name = tex_filename.replace('.tex', '.pdf')
            print(f"Output: {self.output_dir / pdf_name}")
            return True
            
        except FileNotFoundError:
            print("Error: pdflatex not found. Please install texlive-latex-base or equivalent.")
            return False
        finally:
            os.chdir(original_dir)
            
    def clean_output(self):
        """Clean auxiliary LaTeX files."""
        aux_extensions = ['.aux', '.log', '.toc', '.out', '.fls', '.fdb_latexmk']
        
        for ext in aux_extensions:
            for file in self.output_dir.glob(f"*{ext}"):
                file.unlink()
                print(f"Removed: {file.name}")

def main():
    parser = argparse.ArgumentParser(description='Generate DSET book from markdown chapters (V2)')
    parser.add_argument('--source-dir', default='.', help='Source directory containing markdown files')
    parser.add_argument('--output-name', default='dset_book_v2', help='Output filename (without extension)')
    parser.add_argument('--compile', action='store_true', help='Compile LaTeX to PDF')
    parser.add_argument('--clean', action='store_true', help='Clean auxiliary files after compilation')
    
    args = parser.parse_args()
    
    generator = DSETBookGenerator(args.source_dir)
    
    # Generate LaTeX
    tex_filename = f"{args.output_name}.tex"
    if not generator.generate_book(tex_filename):
        sys.exit(1)
        
    # Compile PDF if requested
    if args.compile:
        if not generator.compile_pdf(tex_filename):
            sys.exit(1)
            
        # Clean auxiliary files if requested
        if args.clean:
            generator.clean_output()
            
    print("Book generation complete!")

if __name__ == "__main__":
    main()