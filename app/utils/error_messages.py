"""
Professional Error Messages - User-friendly error responses
"""
from typing import Optional
import re


def get_professional_error_message(
    question: str,
    error_type: str,
    technical_error: Optional[str] = None
) -> str:
    """
    Generate professional, user-friendly error message
    
    Args:
        question: User's original question
        error_type: Type of error (sql_generation, sql_execution, incomplete_query, etc.)
        technical_error: Technical error details (for logging, not shown to user)
    
    Returns:
        Professional error message in user's language
    """
    # Detect user's language (Arabic or English)
    is_arabic = _is_arabic(question)
    
    if error_type == "sql_generation":
        if is_arabic:
            return (
                "عذراً، لا يمكنني الإجابة على هذا السؤال في الوقت الحالي.\n\n"
                "السبب: السؤال غير واضح أو لا توجد بيانات كافية في قاعدة البيانات للإجابة عليه.\n\n"
                "اقتراحات:\n"
                "• حاول إعادة صياغة السؤال بشكل أكثر وضوحاً\n"
                "• تأكد من أن السؤال يتعلق بالبيانات المتوفرة في قاعدة البيانات\n"
                "• استخدم مصطلحات واضحة مثل: 'اعرض'، 'كم عدد'، 'ما هي'، إلخ"
            )
        else:
            return (
                "I apologize, but I cannot answer this question at the moment.\n\n"
                "Reason: The question is unclear or there is insufficient data in the database to answer it.\n\n"
                "Suggestions:\n"
                "• Try rephrasing your question more clearly\n"
                "• Make sure your question relates to the data available in the database\n"
                "• Use clear terms like: 'show', 'how many', 'what are', etc."
            )
    
    elif error_type == "sql_execution" or error_type == "incomplete_query":
        if is_arabic:
            return (
                "عذراً، لا يمكنني الإجابة على هذا السؤال.\n\n"
                "السبب: السؤال غير واضح أو لا توجد بيانات كافية في قاعدة البيانات للإجابة عليه.\n\n"
                "اقتراحات:\n"
                "• حاول إعادة صياغة السؤال بشكل أكثر تحديداً\n"
                "• تأكد من ذكر الجداول أو البيانات التي تريد الاستعلام عنها\n"
                "• مثال: 'اعرض جميع الفئات' أو 'كم عدد الأفلام في كل فئة؟'"
            )
        else:
            return (
                "I apologize, but I cannot answer this question.\n\n"
                "Reason: The question is unclear or there is insufficient data in the database to answer it.\n\n"
                "Suggestions:\n"
                "• Try rephrasing your question more specifically\n"
                "• Make sure to mention the tables or data you want to query\n"
                "• Example: 'Show all categories' or 'How many films are in each category?'"
            )
    
    elif error_type == "no_data":
        if is_arabic:
            return (
                "تم تنفيذ الاستعلام بنجاح، لكن لم يتم العثور على أي بيانات.\n\n"
                "هذا يعني أن قاعدة البيانات لا تحتوي على بيانات تطابق معايير البحث الخاصة بك."
            )
        else:
            return (
                "The query was executed successfully, but no data was found.\n\n"
                "This means the database does not contain any data matching your search criteria."
            )
    
    elif error_type == "general_error":
        if is_arabic:
            return (
                "عذراً، حدث خطأ أثناء معالجة سؤالك.\n\n"
                "السبب: السؤال غير واضح أو لا توجد بيانات كافية للإجابة عليه.\n\n"
                "يرجى المحاولة مرة أخرى أو إعادة صياغة السؤال."
            )
        else:
            return (
                "I apologize, an error occurred while processing your question.\n\n"
                "Reason: The question is unclear or there is insufficient data to answer it.\n\n"
                "Please try again or rephrase your question."
            )
    
    else:
        # Default message
        if is_arabic:
            return (
                "عذراً، لا يمكنني الإجابة على هذا السؤال.\n\n"
                "السبب: السؤال غير واضح أو لا توجد بيانات كافية في قاعدة البيانات للإجابة عليه.\n\n"
                "يرجى المحاولة مرة أخرى أو إعادة صياغة السؤال بشكل أكثر وضوحاً."
            )
        else:
            return (
                "I apologize, but I cannot answer this question.\n\n"
                "Reason: The question is unclear or there is insufficient data in the database to answer it.\n\n"
                "Please try again or rephrase your question more clearly."
            )


def _is_arabic(text: str) -> bool:
    """Detect if text is primarily Arabic"""
    if not text:
        return False
    
    # Count Arabic characters
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    arabic_chars = len(arabic_pattern.findall(text))
    total_chars = len(re.findall(r'[a-zA-Z\u0600-\u06FF]', text))
    
    if total_chars == 0:
        return False
    
    # If more than 30% Arabic characters, consider it Arabic
    return (arabic_chars / total_chars) > 0.3
