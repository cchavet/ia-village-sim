from fpdf import FPDF
import os

class StoryPDF(FPDF):
    def __init__(self, title, author="Gemini AI"):
        super().__init__()
        self.doc_title = title
        self.doc_author = author
        self.set_auto_page_break(auto=True, margin=15)
        
    def header(self):
        # En-tête discret (sauf 1ere page)
        if self.page_no() > 1:
            self.set_font('helvetica', 'I', 8)
            self.cell(0, 10, self.doc_title, 0, 0, 'R')
            self.ln(15)

    def footer(self):
        # Pied de page
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, num, label):
        self.set_font('helvetica', 'B', 16)
        self.cell(0, 10, f"Chapitre {num} : {label}", 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('times', '', 12)
        # Nettoyage du markdown basique (gras/italique non géré parfaitement par FPDF simple, on clean)
        clean_body = body.replace('**', '').replace('*', '') 
        self.multi_cell(0, 8, clean_body)
        self.ln()
    
    def print_chapter(self, num, title, body):
        self.add_page()
        self.chapter_title(num, title)
        self.chapter_body(body)

def publish_book_pdf(title, chapters_list, output_filename="story/Livre_Complet.pdf"):
    """
    Génère un PDF professionnel combinant tous les chapitres.
    chapters_list : liste de strings (texte complet de chaque chapitre).
    """
    os.makedirs(os.path.dirname(output_filename), exist_ok=True)
    
    pdf = StoryPDF(title)
    pdf.set_title(title)
    pdf.set_author("Gemini & Simulation Engine")
    
    # 1. Page Titre
    pdf.add_page()
    pdf.set_font('times', 'B', 24)
    pdf.ln(60)
    pdf.cell(0, 10, title, 0, 1, 'C')
    pdf.set_font('times', 'I', 16)
    pdf.cell(0, 10, "Une épopée générée par IA", 0, 1, 'C')
    pdf.ln(20)
    
    # 2. Sommaire (Mockup pour l'instant, FPDF2 a des outils auto mais restons simples)
    pdf.add_page()
    pdf.set_font('times', 'B', 16)
    pdf.cell(0, 10, "Sommaire", 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('times', '', 12)
    for i, _ in enumerate(chapters_list):
        pdf.cell(0, 10, f"Chapitre {i+1}", 0, 1, 'L')
    
    # 3. Chapitres
    for i, text in enumerate(chapters_list):
        # Extraction Titre si format "**TITRE**"
        lines = text.split('\n')
        title_line = "Suite du récit"
        body_start = 0
        
        # Tentative de parsing simple du titre (souvent ligne 1)
        if lines and "CHAPITRE" in lines[0].upper():
             title_line = lines[0].replace('*', '').strip()
             body_start = 1
        
        content = "\n".join(lines[body_start:])
        pdf.print_chapter(i+1, title_line, content)
        
    pdf.output(output_filename)
    return output_filename
