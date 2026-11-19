from pathlib import Path
path = Path(r'd:\GRATEFUL_WATERSTATION\accounts\views.py')
text = path.read_text(encoding='utf-8')
marker = "    return render(request, 'accounts/product_form.html', {\n"
idx = text.index(marker)
idx2 = text.index('@staff_required', idx)
insert = '''@staff_required
@require_http_methods(["POST"])
def product_delete(request, product_id):

    """Delete a product"""

    product = get_object_or_404(Product, id=product_id)
    product_name = product.name
    product.delete()
    messages.success(request, f'Product "{product_name}" deleted successfully!')
    return redirect('inventory_list')

'''
path.write_text(text[:idx2] + insert + text[idx2:], encoding='utf-8')
