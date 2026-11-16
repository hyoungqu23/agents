def export_rows(rows, selected_ids):
    return [row for row in rows if not selected_ids or row['id'] in selected_ids]
