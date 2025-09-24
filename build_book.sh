#!/bin/bash

# DSET Book Build Script
# Generates a professional PDF book from markdown chapters

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
BOOK_NAME="dset_book"

# Functions
print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE} DSVT (Dual-State Value Theory) Book Generation Script${NC}"
    echo -e "${BLUE}================================${NC}"
    echo
}

print_step() {
    echo -e "${GREEN}[STEP]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    print_step "Checking dependencies..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    print_info "Python 3: $(python3 --version)"
    
    # Check LaTeX
    if ! command -v pdflatex &> /dev/null; then
        print_error "pdflatex is required but not installed."
        print_info "Install with: sudo apt-get install texlive-latex-base texlive-latex-extra"
        exit 1
    fi
    print_info "pdflatex: $(pdflatex --version | head -n1)"
    
    # Check required LaTeX packages
    local packages=("geometry" "fancyhdr" "titlesec" "tocloft" "hyperref" "amsmath")
    for package in "${packages[@]}"; do
        if ! kpsewhich "$package.sty" &> /dev/null; then
            print_warning "LaTeX package '$package' may not be installed"
        fi
    done
    
    echo
}

create_output_dir() {
    print_step "Creating output directory..."
    mkdir -p "$OUTPUT_DIR"
    print_info "Output directory: $OUTPUT_DIR"
    echo
}

generate_latex() {
    print_step "Generating LaTeX from markdown chapters..."
    
    # Use the improved v2 generator
    if ! python3 "$SCRIPT_DIR/generate_book_v2.py" --source-dir "$SCRIPT_DIR" --output-name "$BOOK_NAME"; then
        print_error "Failed to generate LaTeX"
        exit 1
    fi
    
    print_info "LaTeX file generated: $OUTPUT_DIR/${BOOK_NAME}.tex"
    echo
}

compile_pdf() {
    print_step "Compiling PDF..."
    
    cd "$OUTPUT_DIR"
    
    # First pass
    print_info "Running pdflatex (pass 1/2)..."
    pdflatex -interaction=nonstopmode "${BOOK_NAME}.tex" > "${BOOK_NAME}_compile.log" 2>&1
    local first_exit_code=$?
    
    # Check if PDF was created (compilation might succeed with warnings)
    if [ ! -f "${BOOK_NAME}.pdf" ] && [ $first_exit_code -ne 0 ]; then
        print_error "First pdflatex pass failed. Check ${BOOK_NAME}_compile.log for details."
        tail -20 "${BOOK_NAME}_compile.log"
        exit 1
    fi
    
    # Second pass for cross-references and TOC
    print_info "Running pdflatex (pass 2/2)..."
    pdflatex -interaction=nonstopmode "${BOOK_NAME}.tex" >> "${BOOK_NAME}_compile.log" 2>&1
    local second_exit_code=$?
    
    # Check final PDF exists
    if [ ! -f "${BOOK_NAME}.pdf" ]; then
        print_error "Second pdflatex pass failed. Check ${BOOK_NAME}_compile.log for details."
        tail -20 "${BOOK_NAME}_compile.log"
        exit 1
    fi
    
    # Show warnings if there were any
    if [ $first_exit_code -ne 0 ] || [ $second_exit_code -ne 0 ]; then
        print_warning "Compilation completed with warnings. Check ${BOOK_NAME}_compile.log for details."
    fi
    
    cd "$SCRIPT_DIR"
    
    if [ -f "$OUTPUT_DIR/${BOOK_NAME}.pdf" ]; then
        print_info "PDF compiled successfully: $OUTPUT_DIR/${BOOK_NAME}.pdf"
    else
        print_error "PDF file not found after compilation"
        exit 1
    fi
    
    echo
}

clean_auxiliary_files() {
    print_step "Cleaning auxiliary files..."
    
    cd "$OUTPUT_DIR"
    rm -f *.aux *.log *.toc *.out *.fls *.fdb_latexmk
    cd "$SCRIPT_DIR"
    
    print_info "Auxiliary files cleaned"
    echo
}

show_results() {
    print_step "Build completed successfully!"
    
    local pdf_size=$(du -h "$OUTPUT_DIR/${BOOK_NAME}.pdf" | cut -f1)
    local page_count=$(pdfinfo "$OUTPUT_DIR/${BOOK_NAME}.pdf" 2>/dev/null | grep "Pages:" | awk '{print $2}' || echo "Unknown")
    
    echo -e "${GREEN}Output Files:${NC}"
    echo "  📄 LaTeX source: $OUTPUT_DIR/${BOOK_NAME}.tex"
    echo "  📖 PDF book: $OUTPUT_DIR/${BOOK_NAME}.pdf"
    echo "  📊 File size: $pdf_size"
    echo "  📃 Pages: $page_count"
    echo
    
    # Check if we can open the PDF
    if command -v xdg-open &> /dev/null; then
        echo -e "${BLUE}To open the PDF:${NC}"
        echo "  xdg-open \"$OUTPUT_DIR/${BOOK_NAME}.pdf\""
    elif command -v open &> /dev/null; then
        echo -e "${BLUE}To open the PDF:${NC}"
        echo "  open \"$OUTPUT_DIR/${BOOK_NAME}.pdf\""
    fi
    echo
}

# Main execution
main() {
    print_header
    
    # Parse command line arguments
    CLEAN_ONLY=false
    FORCE_REBUILD=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --clean)
                CLEAN_ONLY=true
                shift
                ;;
            --force)
                FORCE_REBUILD=true
                shift
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo "Options:"
                echo "  --clean     Clean output directory and exit"
                echo "  --force     Force rebuild even if PDF exists"
                echo "  --help, -h  Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Clean only mode
    if [ "$CLEAN_ONLY" = true ]; then
        print_step "Cleaning output directory..."
        rm -rf "$OUTPUT_DIR"
        print_info "Output directory cleaned"
        exit 0
    fi
    
    # Check if PDF already exists and force not specified
    if [ -f "$OUTPUT_DIR/${BOOK_NAME}.pdf" ] && [ "$FORCE_REBUILD" != true ]; then
        print_info "PDF already exists: $OUTPUT_DIR/${BOOK_NAME}.pdf"
        print_info "Use --force to rebuild or --clean to remove"
        exit 0
    fi
    
    # Main build process
    check_dependencies
    create_output_dir
    generate_latex
    compile_pdf
    clean_auxiliary_files
    show_results
}

# Run main function with all arguments
main "$@"