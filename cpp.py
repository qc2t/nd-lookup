if not results.empty:
                st.success(f"✅ 找到 {len(results)} 条相关记录")
                
                # 遍历查询到的每一条结果，用卡片形式展示
                for _, row in results.iterrows():
                    with st.container():
                        # 创建一个美观的边框容器
                        st.markdown(f"### 📦 轴号：{row['轴号']}")
                        
                        # 第一行：基础信息
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.write(f"**材质：** {row.get('材质', 'N/A')}")
                            st.write(f"**炉号：** {row.get('炉号', 'N/A')}")
                        with col2:
                            st.write(f"**证件编号：** {row.get('证件编号', 'N/A')}")
                            st.write(f"**图号：** {row.get('图号', 'N/A')}")
                        with col3:
                            st.write(f"**验船师：** {row.get('验船师', 'N/A')}")
                            st.write(f"**船检时间：** {row.get('船检时间', 'N/A')}")
                        
                        # 第二行：补充信息（如果有）
                        st.markdown(f"""
                        > **船检控制号：** {row.get('船检控制号', '无')}  
                        > **证书取件时间：** {row.get('证书取件时间', '未取件')}
                        """)
                        st.divider() # 分割线