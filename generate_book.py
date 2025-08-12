#!/usr/bin/env python3
"""
DSVM Book Generator

Converts markdown chapters to a professional LaTeX book format.
Handles chapter ordering, markdown to LaTeX conversion, and book compilation.
"""

import os
import re
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

class DSVMBookGenerator:
    def __init__(self, source_dir: str = "."):
        self.source_dir = Path(source_dir)
        self.output_dir = self.source_dir / "output"
        self.template_file = self.source_dir / "book_template.tex"
        
        # Chapter ordering based on CLAUDE.md structure
        self.chapter_order = [
            ("abstract.md", "Abstract"),
            ("introduction.md", "Introduction"),
            ("chapter_01_foundations.md", "Chapter 1: Foundations of the Dual-State Model"),
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
        
    def clean_latex_text(self, text: str) -> str:
        """Clean and escape text for LaTeX."""
        # Basic character escaping
        text = text.replace("\\", "\\textbackslash ")
        text = text.replace("&", "\\&")
        text = text.replace("%", "\\%")
        text = text.replace("$", "\\$")
        text = text.replace("#", "\\#")
        text = text.replace("^", "\\textasciicircum ")
        text = text.replace("_", "\\_")
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        text = text.replace("~", "\\textasciitilde ")
        
        return text
        
    def convert_markdown_to_latex(self, markdown_content: str) -> str:
        """Convert markdown content to LaTeX format."""
        lines = markdown_content.split('\n')
        latex_lines = []
        in_code_block = False
        
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
                
            # Skip the main title (handled separately)
            if line.startswith('# ') and not line.startswith('## '):
                continue
                
            # Convert headers
            if line.startswith('#### '):
                latex_lines.append(f"\\paragraph{{{self.clean_latex_text(line[5:])}}}")
            elif line.startswith('### '):
                latex_lines.append(f"\\subsubsection{{{self.clean_latex_text(line[4:])}}}")
            elif line.startswith('## '):
                latex_lines.append(f"\\section{{{self.clean_latex_text(line[3:])}}}")
                
            # Convert bold and italic
            elif line.strip():
                # Handle bold **text**
                line = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', line)
                # Handle italic *text*
                line = re.sub(r'\*(.*?)\*', r'\\textit{\1}', line)
                # Handle inline code `code`
                line = re.sub(r'`(.*?)`', r'\\texttt{\1}', line)
                
                # Convert bullet points
                if line.strip().startswith('- '):
                    if not latex_lines or not latex_lines[-1].strip().startswith('\\item'):
                        latex_lines.append('\\begin{itemize}')
                    latex_lines.append(f"\\item {self.clean_latex_text(line[2:])}")
                elif latex_lines and latex_lines[-1].strip().startswith('\\item') and not line.strip().startswith('- '):
                    latex_lines.append('\\end{itemize}')
                    latex_lines.append(self.clean_latex_text(line))
                else:
                    latex_lines.append(self.clean_latex_text(line))
            else:
                # Close itemize if we hit empty line after items
                if latex_lines and latex_lines[-1].strip().startswith('\\item'):
                    latex_lines.append('\\end{itemize}')
                latex_lines.append('')
                
        # Close any remaining itemize
        if latex_lines and latex_lines[-1].strip().startswith('\\item'):
            latex_lines.append('\\end{itemize}')
            
        return '\n'.join(latex_lines)
        
    def process_chapter(self, filename: str, title: str) -> Optional[str]:
        """Process a single chapter file."""
        file_path = self.source_dir / filename
        
        if not file_path.exists():
            print(f"Warning: Chapter file {filename} not found, skipping...")
            return None
            
        print(f"Processing: {filename} -> {title}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Convert to LaTeX
        latex_content = self.convert_markdown_to_latex(content)
        
        # Handle special cases
        if filename == "abstract.md":
            return latex_content
        elif filename == "introduction.md":
            return latex_content
        elif filename.startswith("appendix"):
            return f"\\appendix\n\\chapter{{{title[11:]}}}\n{latex_content}"  # Remove "Appendix A: "
        else:
            return f"\\chapter{{{title[10:]}}}\n{latex_content}"  # Remove "Chapter X: "
            
    def generate_book(self, output_filename: str = "dsvm_book.tex") -> bool:
        """Generate the complete book."""
        print("Generating DSVM Book...")
        
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
        
    def compile_pdf(self, tex_filename: str = "dsvm_book.tex") -> bool:
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
                    text=True
                )
                
                if result.returncode != 0:
                    print(f"Error in pdflatex pass {i+1}:")
                    print(result.stdout)
                    print(result.stderr)
                    return False
                    
            print("PDF compilation successful!")
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
    parser = argparse.ArgumentParser(description='Generate DSVM book from markdown chapters')
    parser.add_argument('--source-dir', default='.', help='Source directory containing markdown files')
    parser.add_argument('--output-name', default='dsvm_book', help='Output filename (without extension)')
    parser.add_argument('--compile', action='store_true', help='Compile LaTeX to PDF')
    parser.add_argument('--clean', action='store_true', help='Clean auxiliary files after compilation')
    
    args = parser.parse_args()
    
    generator = DSVMBookGenerator(args.source_dir)
    
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