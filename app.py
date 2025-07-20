import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# 页面配置
st.set_page_config(
    page_title="法律关系抽取：数据标注工具",
    page_icon="📝",
    layout="centered"
)

# 初始化session状态
if "json_data" not in st.session_state:
    st.session_state.json_data = None

# 页面标题
st.title("📝法律关系抽取：数据标注工具")
st.markdown("""---""")

# 在侧边栏添加上传功能
with st.sidebar:
    st.header("📂 文件处理")
    # 默认文件路径
    DEFAULT_JSON_PATH = "./test1_v4.json"
    
    # 上传JSON文件
    uploaded_file = st.file_uploader("上传JSON文件", type=["json"], key="json_uploader")

    # 如果没有上传文件，尝试加载默认文件
    if uploaded_file is None:
        try:
            with open(DEFAULT_JSON_PATH, 'r', encoding='utf-8') as f:
                st.session_state.json_data = json.load(f)
                # st.session_state.edited_data = st.session_state.json_data.copy()
            st.success(f"已自动加载默认文件: {DEFAULT_JSON_PATH}")
        except FileNotFoundError:
            st.warning("未找到默认JSON文件，请上传文件")
        except Exception as e:
            st.error(f"解析默认JSON文件失败: {str(e)}")
    elif uploaded_file is not None:
        try:
            st.session_state.json_data = json.load(uploaded_file)
            # st.session_state.edited_data = st.session_state.json_data.copy()
            st.success("上传的JSON文件加载成功！")
        except Exception as e:
            st.error(f"解析上传的JSON文件失败: {str(e)}")
    
    if isinstance(st.session_state.json_data, list) and len(st.session_state.json_data) > 0:
        # 初始化分页状态
        if "current_page" not in st.session_state:
            st.session_state.current_page = 0
            st.session_state.current_item = 0
        
        st.markdown(f"**总数据条数**: {len(st.session_state.json_data)}")
        st.session_state.current_item = st.number_input(
            "数据编号", 
            min_value=0, 
            max_value=len(st.session_state.json_data)-1,
            value=st.session_state.current_item,
            step=1
        )
        
        current_dict = st.session_state.json_data[st.session_state.current_item]
        
        if current_dict['edited'] == 1:
            st.success("此条数据已标注")
            

# 在显示和编辑JSON内容部分修改
if st.session_state.json_data is not None:
    
    if isinstance(st.session_state.json_data, list) and len(st.session_state.json_data) > 0:
        
        st.subheader(f"数据id：{st.session_state.current_item}")
        
        if 'TITLE' in current_dict:
            st.subheader(f"标题")
            st.text(f"{current_dict['TITLE']}")
        
        if 'ss' in current_dict:
            st.subheader(f"法庭认定事实")
            # st.text(f"{current_dict['SS']}")
            content_lines = len(current_dict['ss'])
            edited_ss = st.text_area(
                "编辑事实内容", 
                value=current_dict['ss'],
                key=f"ss_editor_{st.session_state.current_item}",
                label_visibility='hidden',
                height=int(content_lines)
            )
        
        if 'yj' in current_dict:
            st.subheader(f"法庭意见")
            # st.text(f"{current_dict['YJ']}")
            content_lines = len(current_dict['yj'])
            edited_yj = st.text_area(
                "编辑意见内容", 
                value=current_dict['yj'],
                key=f"yj_editor_{st.session_state.current_item}",
                label_visibility='hidden',
                height=int(content_lines*0.7)
            )
         
        if 'subject-object' in current_dict:
            st.subheader("主客体")
            subject_object = current_dict['subject-object']
            
            # 将subject-object转换为DataFrame格式
            data = []
            for key, value in subject_object.items():
                if isinstance(value, dict):
                    row = value.copy()
                else:
                    for v in value.replace("'",'"').split("\n"):
                        try:
                            if v != '':
                                row = json.loads(v)
                                row['主体'] = str(row.get('主体', ''))
                                row['客体'] = str(row.get('客体', ''))
                                if '内容' not in row:
                                    row['内容'] = ''
                            else:
                                continue
                        except:
                            row = {"主体": "", "客体": "", "内容": v}
                        row['关系名称'] = key
                        data.append(row)
            
            df = pd.DataFrame(data)
            df = df[['关系名称', '主体', '客体', '内容']]  # 调整列顺序
            # 使用data_editor编辑数据
            edited_df = st.data_editor(
                df,
                num_rows="dynamic",
                use_container_width=True,
                key=f"subject_object_editor_{st.session_state.current_item}"
            )
            # st.session_state.json_data[st.session_state.current_item]['edited'] = 1
            # 将编辑后的数据转换回原始格式
        # 在初始化session状态部分添加
        if "new_data" not in st.session_state:
            st.session_state.new_data = []
        if "new_id" not in st.session_state:
            st.session_state.new_id = set()
        
        # 修改保存按钮部分的代码
        st.warning(f"当前数据id：{st.session_state.current_item}，请注意保存")
        if st.button("**保存修改**"):
            if not df.equals(edited_df):
                new_item = {}
                edited_subject_object = {}
                for _, row in edited_df.iterrows():
                    key = row['关系名称']
                    value = {
                        "主体": row['主体'],
                        "客体": row['客体'],
                        "内容": row['内容']
                    }
                    edited_subject_object[key] = edited_subject_object.get(key,[])
                    edited_subject_object[key].append(value)
                new_item['uniqid'] = current_dict['uniqid']
                new_item['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S") 
                new_item['edited'] = 1
                new_item['subject-object'] = edited_subject_object
                st.session_state.new_data.append(new_item)
                st.session_state.new_id.add(st.session_state.current_item)
                st.session_state.json_data[st.session_state.current_item]['edited'] = 1
                st.success("修改已保存！")
            else:
                st.warning("⚠️⚠️未做修改⚠️⚠️")
                

with st.sidebar:
    st.markdown("""---""")
    st.success(f"已完成的标注id：{list(set(st.session_state.new_id))}")
    st.error("⚠️⚠️请在完成标记后下载标记结果文件⚠️⚠️")
    # st.subheader("下载标注记录文件")
    json_str = json.dumps(st.session_state.new_data, ensure_ascii=False, indent=2)
    st.download_button(
        label="下载标注结果文件",
        data=json_str,
        file_name="edited_data.json",
        mime="application/json"
    )
