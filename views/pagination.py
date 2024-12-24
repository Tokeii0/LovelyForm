class PaginationMixin:
    def prev_page(self):
        """前一页"""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_table()

    def next_page(self):
        """后一页"""
        page_size = self.page_size_spin.value() if hasattr(self, 'page_size_spin') else self.page_size
        total_pages = (len(self.data_manager.df) - 1) // page_size + 1
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_table()

    def update_page_size(self):
        """更新每页显示的行数"""
        self.page_size = self.page_size_spin.value()
        self.current_page = 0
        self.update_table()

    def update_page_label(self):
        """更新页码显示标签"""
        if not hasattr(self, 'page_label') or self.data_manager.df.empty:
            return
            
        page_size = self.page_size_spin.value() if hasattr(self, 'page_size_spin') else self.page_size
        total_pages = (len(self.data_manager.df) - 1) // page_size + 1
        current_page = self.current_page + 1
        self.page_label.setText(f"页码: {current_page}/{total_pages}")

    def update_page_jump_range(self):
        """更新页码跳转范围"""
        if self.data_manager.df.empty:
            self.page_jump_spin.setRange(1, 1)
            return
            
        page_size = self.page_size_spin.value()
        total_pages = (len(self.data_manager.df) - 1) // page_size + 1
        self.page_jump_spin.setRange(1, total_pages)
        self.page_jump_spin.setValue(self.current_page + 1)

    def jump_to_page(self):
        """跳转到指定页码"""
        target_page = self.page_jump_spin.value() - 1
        if target_page != self.current_page:
            self.current_page = target_page
            self.update_table()
