import sys
import os
from pathlib import Path

# Add parent directory to path to import pdf_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import streamlit as st

from pdf_utils import extract_item_analysis, convert_df_to_pdf, convert_df_to_styled_excel

st.set_page_config(page_title="HKDSE Statistical Report Data Extraction | HKDSE學校統計報告 數據提取工具", page_icon="🧭", layout="wide")
st.title("📌 自訂項目分析 | Custom Item Analysis")

if "item_custom_cols" not in st.session_state:
    st.session_state.item_custom_cols = []
if "item_col_options_history" not in st.session_state:
    st.session_state.item_col_options_history = {}
if "item_custom_values" not in st.session_state:
    st.session_state.item_custom_values = {}
if "mcq_custom_values" not in st.session_state:
    st.session_state.mcq_custom_values = {}
if "item_clear_inputs" not in st.session_state:
    st.session_state.item_clear_inputs = False
if "item_save_note" not in st.session_state:
    st.session_state.item_save_note = ""
if "item_cutoff_high" not in st.session_state:
    st.session_state.item_cutoff_high = 70
if "item_cutoff_low" not in st.session_state:
    st.session_state.item_cutoff_low = 30
if "item_exp_high" not in st.session_state:
    st.session_state.item_exp_high = 80
if "item_exp_inter" not in st.session_state:
    st.session_state.item_exp_inter = 60
if "item_exp_low" not in st.session_state:
    st.session_state.item_exp_low = 40
if "item_sort_levels" not in st.session_state:
    # Each level is a dict: {"col": column_name, "order": "desc"/"asc"}
    st.session_state.item_sort_levels = [{"col": "row_index", "order": "desc"}]
if "item_quick_filter_below" not in st.session_state:
    st.session_state.item_quick_filter_below = False
if "item_quick_filter_high" not in st.session_state:
    st.session_state.item_quick_filter_high = False
if "item_quick_filter_unassigned" not in st.session_state:
    st.session_state.item_quick_filter_unassigned = False
if "item_preset_sort" not in st.session_state:
    st.session_state.item_preset_sort = "None | 自訂 Custom"

st.page_link("app.py", label="返回主頁 | Main Page", icon="⬅️")

if "processed_item_df" not in st.session_state or st.session_state.processed_item_df is None:
    source_pdf_bytes = st.session_state.get("source_pdf_bytes")
    if isinstance(source_pdf_bytes, (bytes, bytearray)) and source_pdf_bytes:
        st.session_state.processed_item_df = extract_item_analysis(source_pdf_bytes)

if "processed_item_df" not in st.session_state or st.session_state.processed_item_df is None:
    st.warning("未找到項目分析資料，請回到主頁完成上載。| No item analysis data found yet. Please upload the report in the main page.")
    st.stop()

df_item_c = st.session_state.processed_item_df.copy()
source_name = st.session_state.get("source_pdf_name", "未命名檔案")
st.success(f"已載入主頁資料 Data Loaded from: {source_name}")

if not df_item_c.empty:
    if "row_index" not in df_item_c.columns:
        df_item_c.insert(0, "row_index", range(1, len(df_item_c) + 1))
    if "題號" not in df_item_c.columns:
        df_item_c.insert(1, "題號", df_item_c.get("Item", range(1, len(df_item_c) + 1)))
    if "Item" in df_item_c.columns:
        df_item_c = df_item_c.drop(columns=["Item"])

    sel_q = None

    st.markdown("---")
    st.info("🏷️ 1. 建立自訂欄位並為題目設定分類 Create Custom Fields and Set Categories for Questions")
    col1, col2, col3 = st.columns(3, border=True)

    with col1:
        st.subheader("1.1 建立自訂欄位 item_custom_cols")
        st.caption("自訂欄位可用於為每題設定不同的分類，例如「試卷」、「題型」、「難度」等。")
        with st.form("item_add_field_form", clear_on_submit=True, border=False):
            new_col = st.text_input("輸入新自訂欄位名稱 | Enter New Custom Field Name", key="new_col_input_item")
            submitted = st.form_submit_button("➕ 新增欄位 Add Field")
            if submitted:
                new_col = new_col.strip()
                if not new_col:
                    st.warning("欄位名稱不可為空。| Field name cannot be empty.")
                elif new_col in st.session_state.item_custom_cols:
                    st.warning("此欄位已存在。| This field already exists.")
                elif len(st.session_state.item_custom_cols) >= 6:
                    st.warning("⚠️ 超過欄位數量限制 Field limit exceeded.")
                else:
                    st.session_state.item_custom_cols.append(new_col)
                    st.session_state.item_col_options_history.setdefault(new_col, [])

        if st.session_state.item_custom_cols:
            st.success(f"已建立欄位 | Created Fields: {', '.join(st.session_state.item_custom_cols)}")
            
            with st.expander("⚙️ 進階操作 Advanced Operations"):
                st.caption("刪除欄位 Delete Field")
                col_to_delete = st.selectbox("選擇要刪除的欄位 | Select Field to Delete", [""] + st.session_state.item_custom_cols, key="item_delete_field_select")
                if col_to_delete:
                    affected_count = sum(1 for idx in st.session_state.item_custom_values if col_to_delete in st.session_state.item_custom_values.get(idx, {}))
                    st.warning(f"此欄位已被 {affected_count} 題使用，刪除後會同時移除該欄位的所有分類設定。| This field is used by {affected_count} question(s). All related data will be deleted.")
                    
                    confirm_delete_field = st.checkbox("我明白刪除後不能復原 I understand deletion is irreversible", key=f"confirm_delete_field_{col_to_delete}")
                    if confirm_delete_field:
                        if st.button("⚠️ 確認刪除欄位 Confirm Delete Field", key=f"item_delete_field_btn_{col_to_delete}"):
                            st.session_state.item_custom_cols.remove(col_to_delete)
                            if col_to_delete in st.session_state.item_col_options_history:
                                del st.session_state.item_col_options_history[col_to_delete]
                            for idx in st.session_state.item_custom_values:
                                st.session_state.item_custom_values[idx].pop(col_to_delete, None)
                            st.success(f"已刪除欄位「{col_to_delete}」及其相關資料。| Field '{col_to_delete}' and related data deleted.")
                            st.rerun()

    with col2:
        st.subheader("1.2 管理欄位分類選項 item_col_options_history")
        st.caption("為每個自訂欄位管理分類選項。")
        if not st.session_state.item_custom_cols:
            st.warning("尚未建立任何自訂欄位，請先在 1.1 區建立。| No custom fields yet.")
        else:
            selected_option_field = st.selectbox("選擇要管理的欄位 | Select Field to Manage", st.session_state.item_custom_cols, key="item_option_field_select")
            
            st.caption("➕ 新增分類 Add Options")
            with st.form("item_add_option_form", clear_on_submit=True, border=False):
                new_options_raw = st.text_input("輸入新分類，逗號分隔 | Enter new option(s), comma-separated", key="new_item_option_input")
                add_options = st.form_submit_button("➕ 新增 Add")
                if add_options:
                    candidates = [opt.strip() for opt in new_options_raw.split(",") if opt.strip()]
                    added = []
                    skipped = []
                    for opt in candidates:
                        if opt in st.session_state.item_col_options_history[selected_option_field]:
                            skipped.append(opt)
                        else:
                            st.session_state.item_col_options_history[selected_option_field].append(opt)
                            added.append(opt)
                    if added:
                        st.success(f"已新增: {', '.join(added)}")
                        st.rerun()
                    if skipped:
                        st.info(f"已略過重複: {', '.join(skipped)}")
                    if not added and not skipped:
                        st.warning("未輸入有效分類。| No valid options entered.")

            with st.container(border=True):
                st.markdown("**欄位下的子類別 | Field Options**")
                for field in st.session_state.item_custom_cols:
                    opts = st.session_state.item_col_options_history.get(field, [])
                    if opts:
                        st.markdown(f"- **{field}**: {', '.join(opts)}")
                    else:
                        st.markdown(f"- **{field}**: 尚未設定選項 | No options set")

            
            with st.expander("⚙️ 進階操作 Advanced Operations"):
                st.caption("刪除分類 Delete Option")
                history_opts = st.session_state.item_col_options_history.get(selected_option_field, [])
                if history_opts:
                    opt_to_delete = st.selectbox("選擇要刪除的分類 | Select Option to Delete", [""] + history_opts, key="item_delete_option_select")
                    if opt_to_delete:
                        affected_count = sum(1 for idx in st.session_state.item_custom_values if st.session_state.item_custom_values.get(idx, {}).get(selected_option_field) == opt_to_delete)
                        st.warning(f"此分類已被 {affected_count} 題使用，刪除後這些題目的值會被清空。| This option is used by {affected_count} question(s). Their values will be cleared.")
                        
                        confirm_delete_opt = st.checkbox("我明白刪除後不能復原 I understand deletion is irreversible", key=f"confirm_delete_opt_{selected_option_field}_{opt_to_delete}")
                        if confirm_delete_opt:
                            if st.button("⚠️ 確認刪除分類 Confirm Delete Option", key=f"item_delete_option_btn_{selected_option_field}_{opt_to_delete}"):
                                st.session_state.item_col_options_history[selected_option_field].remove(opt_to_delete)
                                for idx in st.session_state.item_custom_values:
                                    if selected_option_field in st.session_state.item_custom_values[idx]:
                                        if st.session_state.item_custom_values[idx][selected_option_field] == opt_to_delete:
                                            del st.session_state.item_custom_values[idx][selected_option_field]
                                st.success(f"已刪除分類「{opt_to_delete}」及其相關值。| Option '{opt_to_delete}' and related values deleted.")
                                st.rerun()
                else:
                    st.info("此欄位尚無分類可刪除。| No options to delete for this field.")

    with col3:
        st.subheader("1.3 為題目填入分類 item_custom_values")
        st.caption("選擇題目後，從已設定的分類選項中為每題指定值。")
        question_options = [f"{row['題號']} [{row['row_index']}]" for _, row in df_item_c.iterrows()]
        seq_map = {f"{row['題號']} [{row['row_index']}]": row['row_index'] for _, row in df_item_c.iterrows()}
        sel_qs_display = st.multiselect("選擇題號（可選多於一項） | Select Question(s)", question_options, default=question_options[:1], key="item_q_sel")
        sel_qs = [seq_map[q] for q in sel_qs_display]

        if st.session_state.item_clear_inputs:
            for col in st.session_state.item_custom_cols:
                sel_key = f"sel_item_{col}"
                st.session_state[sel_key] = ""
            st.session_state.item_clear_inputs = False

        if sel_qs_display:
            selected_display = ", ".join(sel_qs_display)
            st.write(f"**編輯 Editing: {selected_display}**")
            all_values = [st.session_state.item_custom_values.get(idx, {}) for idx in sel_qs]
            current_values = {}
            for col in st.session_state.item_custom_cols:
                values_for_col = {v.get(col, "") for v in all_values}
                current_values[col] = values_for_col.pop() if len(values_for_col) == 1 else ""
        else:
            st.warning("請先選擇至少一題。| Please select at least one question first.")
            current_values = {}

        input_results = {}
        for col in st.session_state.item_custom_cols:
            history_opts = st.session_state.item_col_options_history.get(col, [])
            if not history_opts:
                st.warning(f"欄位「{col}」尚未在 1.2 設定分類選項")
            options = [""] + history_opts
            default_idx = 0
            curr_val = current_values.get(col, "")
            if curr_val in options:
                default_idx = options.index(curr_val)
            sel_key = f"sel_item_{col}"
            sel_val = st.selectbox(f"{col}:", options=options, index=default_idx, key=sel_key)
            input_results[col] = sel_val

        if sel_qs_display:
            submit_btn = st.button("📥 儲存設定 Save Settings", key=f"item_save_btn_{'_'.join(str(x) for x in sel_qs)}", use_container_width=True)

            if st.session_state.item_save_note:
                st.caption(st.session_state.item_save_note)

            if submit_btn and sel_qs:
                for idx in sel_qs:
                    st.session_state.item_custom_values.setdefault(idx, {})
                    for col, val in input_results.items():
                        if val:
                            st.session_state.item_custom_values[idx][col] = val
                        else:
                            st.session_state.item_custom_values[idx].pop(col, None)
                st.session_state["item_last_saved_q"] = sel_qs
                st.session_state["item_save_note"] = f"已為以下題目儲存分類設定 | Saved custom category settings for: {selected_display}"
                st.session_state.item_clear_inputs = True
                st.rerun()


    st.markdown("---")
    with st.container():
        st.subheader("2. 校本自訂分析 School-based Customize Analysis")
        cutoff_cols = st.columns(2)
        with cutoff_cols[0]:
            st.subheader("2.1 定義「平均得分率」的分類 | Define Level of Attainment")
            st.caption("根據全港日校考生平均得分率，將題目分成高、中、低三類，以協助學校判斷校本教學重點。")
            st.session_state.item_cutoff_high = st.number_input(
                "高／中得分率分界值（%）| High/Intermediate attainment Cutoff:",
                min_value=0, max_value=100, value=st.session_state.item_cutoff_high, step=1,
                key="item_cutoff_high_input", help="日校得分率高於此值，即視為「高得分率」。"
            )
            st.session_state.item_cutoff_low = st.number_input(
                "中／低得分率分界值（%）| Intermediate/Low attainment Cutoff:",
                min_value=0, max_value=100, value=st.session_state.item_cutoff_low, step=1,
                key="item_cutoff_low_input", help="日校得分率低於此值，即視為「低得分率」。"
            )
            st.markdown(f"**設定:** 高得分率 ≥ {st.session_state.item_cutoff_high}%；中等得分率 {st.session_state.item_cutoff_low}% - {st.session_state.item_cutoff_high}%；低得分率 ≤ {st.session_state.item_cutoff_low}%")
        with cutoff_cols[1]:
            st.subheader("2.2 校本預期平均得分率 | Define School-based Expected Attainment")
            st.caption("依據題目所屬得分率級別，設定校本預期達標門檻，幫助教師判斷哪些題目需要加強跟進。")
            st.session_state.item_exp_high = st.number_input(
                "預期高得分率題目得分率（%）| Expected for High attainment questions:",
                min_value=0, max_value=100, value=st.session_state.item_exp_high, step=1,
                key="item_exp_high_input"
            )
            st.session_state.item_exp_inter = st.number_input(
                "預期中等得分率題目得分率（%）| Expected for Intermediate attainment questions:",
                min_value=0, max_value=100, value=st.session_state.item_exp_inter, step=1,
                key="item_exp_inter_input"
            )
            st.session_state.item_exp_low = st.number_input(
                "預期低得分率題目得分率（%）| Expected for Low attainment questions:",
                min_value=0, max_value=100, value=st.session_state.item_exp_low, step=1,
                key="item_exp_low_input"
            )
            st.caption("示例：若高得分率題目校本預期 80%，該題只要校本得分率 ≥ 80% 則視為達到預期。中/低得分率題目的設定依次類推。")

    if st.session_state.item_cutoff_high <= st.session_state.item_cutoff_low:
        st.error("高／中得分率分界值必須大於中／低得分率分界值，請修正後再查看分析結果。| The high/intermediate cutoff must be greater than the intermediate/low cutoff.")
        st.stop()
    if st.session_state.item_exp_high < st.session_state.item_exp_inter:
        st.warning("警告：高得分率題目的校本預期低於中等得分率題目，請確認設定。| Warning: Expected attainment for High attainment questions is lower than Intermediate attainment questions.")
    if st.session_state.item_exp_inter < st.session_state.item_exp_low:
        st.warning("警告：中等得分率題目的校本預期低於低得分率題目，請確認設定。| Warning: Expected attainment for Intermediate attainment questions is lower than Low attainment questions.")

    df_display = df_item_c.copy()
    for col in st.session_state.item_custom_cols:
        df_display[col] = df_display["row_index"].apply(lambda x: st.session_state.item_custom_values.get(x, {}).get(col, ""))

    # 計算 Day School Attainment
    def get_attainment(rate):
        rate_pct = rate * 100 if rate <= 1 else rate
        if rate_pct >= st.session_state.item_cutoff_high:
            return "High attainment"
        elif rate_pct <= st.session_state.item_cutoff_low:
            return "Low attainment"
        else:
            return "Intermediate attainment"

    df_display["Day School Attainment"] = df_display["Day schools Mean %"].apply(get_attainment)

    # 計算 School-based Expected Attainment
    def get_expected_status(row):
        attainment = row["Day School Attainment"]
        your_rate = row["Your school Mean %"]
        your_rate_pct = your_rate * 100 if your_rate <= 1 else your_rate

        if attainment == "High attainment":
            expected = st.session_state.item_exp_high
        elif attainment == "Intermediate attainment":
            expected = st.session_state.item_exp_inter
        else:  # Low attainment
            expected = st.session_state.item_exp_low

        return "達到校本預期 | Attained" if your_rate_pct >= expected else "低於校本預期，建議關注 | Below Expectation"

    df_display["School-based Expected Attainment"] = df_display.apply(get_expected_status, axis=1)

    count_high = int((df_display["Day School Attainment"] == "High attainment").sum())
    count_inter = int((df_display["Day School Attainment"] == "Intermediate attainment").sum())
    count_low = int((df_display["Day School Attainment"] == "Low attainment").sum())
    count_attained = int((df_display["School-based Expected Attainment"] == "達到校本預期 | Attained").sum())
    count_below = int((df_display["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation").sum())
    total = len(df_display)
    below_pct = f"{(count_below / total * 100):.1f}%" if total else "0%"
    count_below_high = int(((df_display["Day School Attainment"] == "High attainment") & (df_display["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation")).sum())

    settings_summary = st.container()
    with settings_summary:
        st.info(
            f"**目前分析設定 Current Analysis Settings:**\n"
            f"• High/Intermediate cutoff: {st.session_state.item_cutoff_high}%\n"
            f"• Intermediate/Low cutoff: {st.session_state.item_cutoff_low}%\n"
            f"• Expected High: {st.session_state.item_exp_high}%\n"
            f"• Expected Intermediate: {st.session_state.item_exp_inter}%\n"
            f"• Expected Low: {st.session_state.item_exp_low}%"
        )

    kpi_main_cols = st.columns([1, 1])
    with kpi_main_cols[0]:
        kpi_cols_level = st.columns(3)
        kpi_cols_level[0].metric("High attainment 題數", count_high)
        kpi_cols_level[1].metric("Intermediate attainment 題數", count_inter)
        kpi_cols_level[2].metric("Low attainment 題數", count_low)
    with kpi_main_cols[1]:
        kpi_cols_expected = st.columns(2)
        kpi_cols_expected[0].metric("Attained 題數", count_attained)
        kpi_cols_expected[1].metric("Below Expectation 題數", count_below)

    review_text = "目前校本預期分析結果已完成。"
    if count_below:
        review_text += f" 其中 {count_below} 題未達校本預期。"
        if count_below_high:
            review_text += f" 有 {count_below_high} 題屬於高得分率題目，建議優先關注。"
    else:
        review_text += " 所有題目均已達到校本預期。"
    st.info(review_text)

    def status_cell_style(val):
        if val == "High attainment":
            return "background-color: #e8f5e9"
        if val == "Intermediate attainment":
            return "background-color: #e3f2fd"
        if val == "Low attainment":
            return "background-color: #fff8e1"
        if val == "達到校本預期 | Attained":
            return "background-color: #d0f0c0; color: #256029; font-weight: bold"
        if val == "低於校本預期，建議關注 | Below Expectation":
            return "background-color: #ffebee; color: #b71c1c; font-style: italic"
        return ""

    def build_item_export_df(df, for_excel=False):
        export_df = df.copy()
        if not for_excel:
            formatters = {
                "Your school Attem. %": lambda x: f"{x:.1f}" if pd.notna(x) else "",
                "Your school Mean": lambda x: f"{x:.1f}" if pd.notna(x) else "",
                "Your school Mean %": lambda x: f"{x:.1%}" if pd.notna(x) else "",
                "Your school SD": lambda x: f"{x:.1f}" if pd.notna(x) else "",
                "Day schools Attem. %": lambda x: f"{x:.1f}" if pd.notna(x) else "",
                "Day schools Mean": lambda x: f"{x:.1f}" if pd.notna(x) else "",
                "Day schools Mean %": lambda x: f"{x:.1%}" if pd.notna(x) else "",
                "Day schools SD": lambda x: f"{x:.1f}" if pd.notna(x) else "",
            }
            for col, fn in formatters.items():
                if col in export_df.columns:
                    export_df[col] = export_df[col].apply(fn)
        else:
            for col in export_df.columns:
                converted = pd.to_numeric(export_df[col], errors='coerce')
                if not converted.isna().all():
                    export_df[col] = converted
        return export_df

    def build_item_style_map(df):
        style_map = {}
        columns = list(df.columns)
        
        for pos, (_, row) in enumerate(df.iterrows()):
            row_idx = pos
            if "Day School Attainment" in columns:
                col_idx = columns.index("Day School Attainment")
                attendance = row["Day School Attainment"]
                if attendance == "High attainment":
                    style_map[(row_idx, col_idx)] = {"fill": "#d4edda"}
                elif attendance == "Intermediate attainment":
                    style_map[(row_idx, col_idx)] = {"fill": "#e5dbf7"}
                elif attendance == "Low attainment":
                    style_map[(row_idx, col_idx)] = {"fill": "#ffe5cc"}
            if "School-based Expected Attainment" in columns:
                col_idx = columns.index("School-based Expected Attainment")
                expected = row["School-based Expected Attainment"]
                if expected == "達到校本預期 | Attained":
                    style_map[(row_idx, col_idx)] = {"fill": "#d0f0c0", "font_color": "#256029", "bold": True}
                elif expected == "低於校本預期，建議關注 | Below Expectation":
                    style_map[(row_idx, col_idx)] = {"fill": "#ffebee", "font_color": "#b71c1c"}
        return style_map

    priority_df = df_display[
        df_display["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation"
    ]
    st.subheader("Priority Review Items | 優先跟進題目")
    if not priority_df.empty:
        st.dataframe(
            priority_df.style
                .format({
                    "Your school Attem. %": "{:.1f}",
                    "Your school Mean": "{:.1f}",
                    "Your school Mean %": "{:.1%}",
                    "Your school SD": "{:.1f}",
                    "Day schools Attem. %": "{:.1f}",
                    "Day schools Mean": "{:.1f}",
                    "Day schools Mean %": "{:.1%}",
                    "Day schools SD": "{:.1f}"
                })
                .apply(
                    lambda col: col.map(status_cell_style),
                    subset=["Day School Attainment", "School-based Expected Attainment"],
                    axis=0
                ),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("目前沒有低於校本預期的題目。| No items below expectation found.")

    st.write("📊 **總覽表 (本表跟隨以上設定自動更新) | Overview Table (This table updates automatically based on the above settings)**")
    st.session_state["custom_item_overview_df"] = df_display.copy()
    st.dataframe(
        df_display.style
            .format({
                "Your school Attem. %": "{:.1f}",
                "Your school Mean": "{:.1f}",
                "Your school Mean %": "{:.1%}",
                "Your school SD": "{:.1f}",
                "Day schools Attem. %": "{:.1f}",
                "Day schools Mean": "{:.1f}",
                "Day schools Mean %": "{:.1%}",
                "Day schools SD": "{:.1f}"
            })
            .apply(
                lambda col: col.map(status_cell_style),
                subset=["Day School Attainment", "School-based Expected Attainment"],
                axis=0
            ),
        use_container_width=True,
        hide_index=True
    )

    overview_export_df = build_item_export_df(df_display, for_excel=True)
    overview_export_pdf = convert_df_to_pdf(build_item_export_df(df_display, for_excel=False), build_item_style_map(df_display), title="項目分析 | 總覽表 Item Analysis | Overview Table")
    overview_export_excel = convert_df_to_styled_excel(overview_export_df, build_item_style_map(df_display), sheet_name="Item Overview")
    step3_pdf_col, step3_excel_col = st.columns(2)
    with step3_pdf_col:
        st.download_button(
            label="📄 下載 PDF 總覽表 | Download Overview PDF",
            data=overview_export_pdf,
            file_name=f"{source_name.replace('.pdf', '')}_ItemOverview.pdf",
            mime="application/pdf",
            use_container_width=True,
            type="primary",
        )
    with step3_excel_col:
        st.download_button(
            label="📥 下載 Excel 總覽表 | Download Overview Excel",
            data=overview_export_excel,
            file_name=f"{source_name.replace('.pdf', '')}_ItemOverview.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )

    st.markdown("---")
    st.info("↕️ 3. 篩選與排序分析 Filter and Sort Analysis")
    
    # ==================== 3.1 篩選 Filter ====================
    st.subheader("3.1 篩選 Filter")
    
    # --- 常用快捷篩選 Quick Filters ---
    st.markdown("**⚡ 常用快捷篩選 Quick Filters**")
    quick_cols = st.columns([1, 1, 1, 1, 0.5])
    
    with quick_cols[0]:
        if st.button("🔴 只看 Below Expectation | 低於預期", key="item_quick_below", use_container_width=True):
            st.session_state.item_quick_filter_below = True
            st.session_state.item_quick_filter_high = False
            st.session_state.item_quick_filter_unassigned = False
            st.rerun()
    
    with quick_cols[1]:
        if st.button("🟢 只看 High attainment | 高成績", key="item_quick_high", use_container_width=True):
            st.session_state.item_quick_filter_high = True
            st.session_state.item_quick_filter_below = False
            st.session_state.item_quick_filter_unassigned = False
            st.rerun()
    
    with quick_cols[2]:
        if st.button("❓ 只看未分類 | Unassigned", key="item_quick_unassigned", use_container_width=True):
            st.session_state.item_quick_filter_unassigned = True
            st.session_state.item_quick_filter_below = False
            st.session_state.item_quick_filter_high = False
            st.rerun()
    
    with quick_cols[3]:
        if st.button("🔄 清除所有篩選 | Clear All", key="item_clear_all_filters", use_container_width=True):
            st.session_state.item_quick_filter_below = False
            st.session_state.item_quick_filter_high = False
            st.session_state.item_quick_filter_unassigned = False
            st.rerun()
    
    with quick_cols[4]:
        if st.button("⬆️ 重設排序", key="item_reset_sort", use_container_width=True):
            st.session_state.item_sort_levels = [{"col": "row_index", "order": "desc"}]
            st.session_state.item_preset_sort = "None | 自訂 Custom"
            st.rerun()
    
    # --- 進階篩選 Advanced Filters ---
    st.markdown("**🔧 進階篩選 Advanced Filters** (同一欄位內多選 = OR  |  不同欄位間 = AND)")
    
    active_filters = {}
    adv_filter_cols = st.columns(max(len(st.session_state.item_custom_cols) + 2, 2))
    
    for i, col in enumerate(st.session_state.item_custom_cols):
        with adv_filter_cols[i]:
            u_vals = df_display[col].unique()
            u_vals_list = []
            has_empty = False
            for v in u_vals:
                if str(v).strip() == "":
                    has_empty = True
                else:
                    u_vals_list.append(v)
            if has_empty:
                u_vals_list.append("(未設定) | (Unassigned)")
            u_vals_list.sort(key=lambda x: (x == "(未設定) | (Unassigned)", str(x)))
            
            selected = st.multiselect(f"{col}", u_vals_list, key=f"filter_item_{col}", default=[])
            if selected:
                filtered_mask = pd.Series([False] * len(df_display), index=df_display.index)
                for sel_val in selected:
                    if sel_val == "(未設定) | (Unassigned)":
                        filtered_mask = filtered_mask | (df_display[col].astype(str).str.strip() == "")
                    else:
                        filtered_mask = filtered_mask | (df_display[col] == sel_val)
                active_filters[col] = filtered_mask
    
    with adv_filter_cols[len(st.session_state.item_custom_cols)]:
        attainment_vals = sorted([x for x in df_display["Day School Attainment"].unique() if str(x).strip()])
        selected_attainment = st.multiselect("Day School Attainment", attainment_vals, key="filter_item_attainment", default=[])
        if selected_attainment:
            active_filters["Day School Attainment"] = df_display["Day School Attainment"].isin(selected_attainment)
    
    with adv_filter_cols[len(st.session_state.item_custom_cols) + 1]:
        expected_vals = sorted([x for x in df_display["School-based Expected Attainment"].unique() if str(x).strip()])
        selected_expected = st.multiselect("School-based Expected Attainment", expected_vals, key="filter_item_expected", default=[])
        if selected_expected:
            active_filters["School-based Expected Attainment"] = df_display["School-based Expected Attainment"].isin(selected_expected)
    
    # Apply quick filters
    final_df = df_display.copy()
    
    if st.session_state.item_quick_filter_below:
        final_df = final_df[final_df["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation"]
        active_filters["[Quick] Below Expectation"] = True
    
    if st.session_state.item_quick_filter_high:
        final_df = final_df[final_df["Day School Attainment"] == "High attainment"]
        active_filters["[Quick] High attainment"] = True
    
    if st.session_state.item_quick_filter_unassigned:
        unassigned_mask = pd.Series([False] * len(final_df), index=final_df.index)
        for col in st.session_state.item_custom_cols:
            unassigned_mask = unassigned_mask | (final_df[col].astype(str).str.strip() == "")
        final_df = final_df[unassigned_mask]
        active_filters["[Quick] Unassigned"] = True
    
    # Apply advanced filters
    for col, filter_mask in active_filters.items():
        if not col.startswith("[Quick]") and isinstance(filter_mask, pd.Series):
            final_df = final_df[filter_mask]
    
    # Display active filters summary
    st.markdown("**📋 目前已啟用篩選 Active Filters**")
    filter_summary_parts = []
    
    if st.session_state.item_quick_filter_below:
        filter_summary_parts.append("🔴 Below Expectation")
    if st.session_state.item_quick_filter_high:
        filter_summary_parts.append("🟢 High attainment")
    if st.session_state.item_quick_filter_unassigned:
        filter_summary_parts.append("❓ Unassigned")
    
    for col in st.session_state.item_custom_cols:
        if col in active_filters and isinstance(active_filters[col], pd.Series):
            filter_summary_parts.append(f"{col}: 已篩選")
    
    if "Day School Attainment" in active_filters and isinstance(active_filters["Day School Attainment"], pd.Series):
        filter_summary_parts.append("Day School Attainment: 已篩選")
    
    if "School-based Expected Attainment" in active_filters and isinstance(active_filters["School-based Expected Attainment"], pd.Series):
        filter_summary_parts.append("School-based Expected Attainment: 已篩選")
    
    if filter_summary_parts:
        filter_display = " | ".join(filter_summary_parts)
        st.caption(f"✓ {filter_display}")
    else:
        st.caption("無篩選 | No filters")
    
    # ==================== 3.2 排序 Sort ====================
    st.subheader("3.2 排序 Sort")
    
    def _rerun_on_sort_change():
        st.session_state["_item_sort_rerun_toggle"] = not st.session_state.get("_item_sort_rerun_toggle", False)
    
    # Preset sort options
    preset_sort_options = [
        "None | 自訂 Custom",
        "題號順序 | Question Order",
        "風險優先 | Risk First",
        "教學關注優先 | Teaching Priority"
    ]
    
    preset_idx = preset_sort_options.index(st.session_state.item_preset_sort) if st.session_state.item_preset_sort in preset_sort_options else 0
    preset_sort = st.selectbox("預設排序方案 | Preset Sort Schemes", preset_sort_options, index=preset_idx, key="item_preset_sort_select")
    
    if preset_sort != st.session_state.item_preset_sort:
        st.session_state.item_preset_sort = preset_sort
        if preset_sort == "題號順序 | Question Order":
            st.session_state.item_sort_levels = [{"col": "row_index", "order": "asc"}]
        elif preset_sort == "風險優先 | Risk First":
            st.session_state.item_sort_levels = [
                {"col": "School-based Expected Attainment", "order": "asc"},
                {"col": "Your school Mean %", "order": "asc"}
            ]
        elif preset_sort == "教學關注優先 | Teaching Priority":
            st.session_state.item_sort_levels = [
                {"col": "Day School Attainment", "order": "desc"},
                {"col": "School-based Expected Attainment", "order": "asc"},
                {"col": "Your school Mean %", "order": "asc"}
            ]
        elif preset_sort == "None | 自訂 Custom":
            if len(st.session_state.item_sort_levels) == 0:
                st.session_state.item_sort_levels = [{"col": "row_index", "order": "desc"}]
        _rerun_on_sort_change()
    
    # Manual sort level controls
    if preset_sort == "None | 自訂 Custom":
        st.markdown("**🔧 自訂排序層級 Custom Sort Levels**")
        
        sort_columns_opts = ["row_index", "Your school Mean %", "Day schools Mean %", "Day School Attainment", "School-based Expected Attainment"]
        
        add_col, remove_col = st.columns([1, 2], gap="xxsmall")
        with add_col:
            if st.button("➕ 新增排序欄 Add Level", key="item_add_sort_level"):
                if len(st.session_state.item_sort_levels) < 4:
                    st.session_state.item_sort_levels.append({"col": "row_index", "order": "desc"})
                    _rerun_on_sort_change()
        with remove_col:
            if st.button("➖ 移除排序欄 Remove Level", key="item_remove_sort_level"):
                if len(st.session_state.item_sort_levels) > 1:
                    st.session_state.item_sort_levels.pop()
                    _rerun_on_sort_change()
        
        # Render each sort level
        for i, level in enumerate(st.session_state.item_sort_levels):
            cols = st.columns([1, 1])
            with cols[0]:
                sel = st.selectbox(f"欄位 Field {i+1}", sort_columns_opts, index=sort_columns_opts.index(level.get("col") if level.get("col") in sort_columns_opts else "row_index"), key=f"item_sort_col_{i}", on_change=_rerun_on_sort_change)
                st.session_state.item_sort_levels[i]["col"] = sel
            with cols[1]:
                order = st.radio("", ["由高至低 | Descending Order", "由低至高 | Ascending Order"], index=0 if level.get("order", "desc") == "desc" else 1, horizontal=True, key=f"item_sort_order_{i}", on_change=_rerun_on_sort_change)
                st.session_state.item_sort_levels[i]["order"] = "desc" if "由高至低" in order else "asc"
    
    # Apply multi-level sorting
    try:
        sort_by_list = []
        ascending_list = []
        temp_sort_cols = []
        for idx, lvl in enumerate(st.session_state.item_sort_levels):
            col = lvl.get("col")
            order = lvl.get("order", "desc")
            ascending = True if order == "asc" else False
            
            # Custom handling for categorical ranks
            if col == "Day School Attainment":
                rank_map = {"High attainment": 3, "Intermediate attainment": 2, "Low attainment": 1}
                temp_col = f"___item_sort_key_{idx}"
                final_df[temp_col] = final_df[col].map(rank_map).fillna(0)
                sort_by_list.append(temp_col)
                temp_sort_cols.append(temp_col)
                ascending_list.append(ascending)
            elif col == "School-based Expected Attainment":
                # For risk-first and teaching priority, Below Expectation should come first (lower rank value)
                rank_map = {"低於校本預期，建議關注 | Below Expectation": 1, "達到校本預期 | Attained": 2}
                temp_col = f"___item_sort_key_{idx}"
                final_df[temp_col] = final_df[col].map(rank_map).fillna(0)
                sort_by_list.append(temp_col)
                temp_sort_cols.append(temp_col)
                ascending_list.append(ascending)
            elif col in ["row_index", "Your school Mean %", "Day schools Mean %"]:
                final_df[col] = pd.to_numeric(final_df[col], errors='coerce')
                sort_by_list.append(col)
                ascending_list.append(ascending)
            else:
                sort_by_list.append(col)
                ascending_list.append(ascending)
        
        if sort_by_list:
            final_df = final_df.sort_values(by=sort_by_list, ascending=ascending_list, kind='mergesort')
        
        # cleanup temp cols
        for c in temp_sort_cols:
            if c in final_df.columns:
                final_df = final_df.drop(columns=[c])
    except Exception:
        pass
    
    # ==================== 篩選結果摘要 Filtered Result Summary ====================
    st.markdown("**📊 篩選結果摘要 Filtered Result Summary**")
    
    total_filtered = len(final_df)
    count_below_filtered = int((final_df["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation").sum())
    count_attained_filtered = int((final_df["School-based Expected Attainment"] == "達到校本預期 | Attained").sum())
    
    summary_cols = st.columns(3)
    with summary_cols[0]:
        st.metric("目前篩選題數 | Total Filtered", total_filtered)
    with summary_cols[1]:
        st.metric("Below Expectation 題數", count_below_filtered)
    with summary_cols[2]:
        st.metric("Attained 題數", count_attained_filtered)
    
    # Find most concerned custom column classification
    if st.session_state.item_custom_cols and total_filtered > 0:
        most_below_col = None
        most_below_val = None
        most_below_count = 0
        
        for col in st.session_state.item_custom_cols:
            for val in final_df[col].unique():
                if str(val).strip() != "":
                    mask = (final_df[col] == val) & (final_df["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation")
                    count = mask.sum()
                    if count > most_below_count:
                        most_below_count = count
                        most_below_col = col
                        most_below_val = val
        
        if most_below_col and most_below_count > 0:
            st.info(f"⚠️ 最值得關注 | Most concerning: **{most_below_col}** 中的 **{most_below_val}** 有 **{most_below_count}** 題低於預期")
    
    # ==================== 分組檢視 Group Summary ====================
    st.markdown("**📈 分組檢視 Group Summary**")
    
    group_cols_opts = st.session_state.item_custom_cols + ["Day School Attainment", "School-based Expected Attainment"]
    
    if group_cols_opts:
        selected_group_col = st.selectbox("選擇分組欄位 | Select Group Column", group_cols_opts, key="item_group_select")
        
        if selected_group_col:
            group_summary_data = []
            
            for group_val in sorted(final_df[selected_group_col].unique()):
                group_df = final_df[final_df[selected_group_col] == group_val]
                group_count = len(group_df)
                group_below = int((group_df["School-based Expected Attainment"] == "低於校本預期，建議關注 | Below Expectation").sum())
                group_attained = int((group_df["School-based Expected Attainment"] == "達到校本預期 | Attained").sum())
                
                display_val = group_val if str(group_val).strip() != "" else "(未設定) | (Unassigned)"
                group_summary_data.append({
                    "分組 | Group": display_val,
                    "題數 | Count": group_count,
                    "Below Expectation": group_below,
                    "Attained": group_attained
                })
            
            if group_summary_data:
                group_summary_df = pd.DataFrame(group_summary_data)
                st.dataframe(group_summary_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"此分組欄位沒有資料 | No data for this group column")
    else:
        st.info("尚未建立任何自訂欄位，無法進行分組檢視 | No custom columns created yet")
    
    # ==================== 篩選結果表格 Filtered Results Table ====================
    st.write("📋 **篩選結果表 (Filtered Results Table)**")
    
    if total_filtered > 0:
        st.dataframe(
            final_df.style
                .format({
                    "Your school Attem. %": "{:.1f}",
                    "Your school Mean": "{:.1f}",
                    "Your school Mean %": "{:.1%}",
                    "Your school SD": "{:.1f}",
                    "Day schools Attem. %": "{:.1f}",
                    "Day schools Mean": "{:.1f}",
                    "Day schools Mean %": "{:.1%}",
                    "Day schools SD": "{:.1f}"
                })
                .apply(
                    lambda col: col.map(status_cell_style),
                    subset=["Day School Attainment", "School-based Expected Attainment"],
                    axis=0
                ),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("目前篩選無結果 | No results match current filters")
    
    # ==================== 匯出 Export ====================
    if total_filtered > 0:
        export_df_pdf = build_item_export_df(final_df, for_excel=False)
        export_df_excel = build_item_export_df(final_df, for_excel=True)
        style_map = build_item_style_map(final_df)
        
        # Build dynamic PDF title with filter and sort info
        filter_info = []
        if st.session_state.item_quick_filter_below:
            filter_info.append("Below Expectation")
        if st.session_state.item_quick_filter_high:
            filter_info.append("High attainment")
        if st.session_state.item_quick_filter_unassigned:
            filter_info.append("Unassigned")
        
        for col in st.session_state.item_custom_cols:
            if col in active_filters and isinstance(active_filters[col], pd.Series):
                filter_info.append(f"{col}: selected")
        
        if "Day School Attainment" in active_filters and isinstance(active_filters["Day School Attainment"], pd.Series):
            filter_info.append("Day School Attainment: selected")
        
        if "School-based Expected Attainment" in active_filters and isinstance(active_filters["School-based Expected Attainment"], pd.Series):
            filter_info.append("School-based Expected Attainment: selected")
        
        filter_str = " | ".join(filter_info) if filter_info else "No filters"
        
        # describe sort levels
        sort_descs = [f"{lvl.get('col')} ({'asc' if lvl.get('order')=='asc' else 'desc'})" for lvl in st.session_state.item_sort_levels]
        sort_str = " > ".join(sort_descs) if sort_descs else "row_index (desc)"
        pdf_title = f"項目分析 | Item Analysis | Filters: {filter_str} | Sort: {sort_str}"
        
        pdf_bytes = convert_df_to_pdf(export_df_pdf, style_map, title=pdf_title)
        excel_bytes = convert_df_to_styled_excel(export_df_excel, style_map, sheet_name="Item Filtered")
        
        col_pdf, col_excel = st.columns(2)
        with col_pdf:
            st.download_button(
                label="📄 下載 PDF 篩選表 | Download Filtered PDF",
                data=pdf_bytes,
                file_name=f"{source_name.replace('.pdf', '')}_ItemFiltered.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary",
            )
        with col_excel:
            st.download_button(
                label="📥 下載 Excel 篩選表 | Download Filtered Excel",
                data=excel_bytes,
                file_name=f"{source_name.replace('.pdf', '')}_ItemFiltered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )

else:
    st.error("找不到可用的項目分析資料。 | No item analysis data available.")

st.markdown("---")
