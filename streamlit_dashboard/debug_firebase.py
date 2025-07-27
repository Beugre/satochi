#!/usr/bin/env python3
"""
🔍 TEST DEBUG STREAMLIT FIREBASE
Test direct dans l'environnement Streamlit pour déboguer les logs
"""

import streamlit as st

st.title("🔍 Debug Firebase - Test Direct")

try:
    from firebase_config import StreamlitFirebaseConfig
    st.success("✅ Import firebase_config réussi!")
    
    # Test de connexion
    firebase_config = StreamlitFirebaseConfig()
    st.success("✅ Initialisation Firebase réussie!")
    
    # Test direct de récupération des logs
    st.subheader("📋 Test direct get_logs_data")
    
    if st.button("🔍 Tester get_logs_data"):
        try:
            logs_data = firebase_config.get_logs_data(limit=5)
            st.write(f"📊 Nombre de logs récupérés: {len(logs_data)}")
            
            if logs_data:
                st.success("✅ Logs trouvés!")
                for i, log in enumerate(logs_data[:3], 1):
                    st.write(f"**Log {i}:**")
                    st.json(log)
            else:
                st.warning("⚠️ Aucun log récupéré par get_logs_data")
                
                # Test direct de la collection
                st.subheader("🔍 Test direct de la collection")
                try:
                    logs_ref = firebase_config.db.collection('rsi_scalping_logs')
                    direct_logs = logs_ref.limit(3).stream()
                    
                    direct_data = []
                    for log in direct_logs:
                        log_dict = log.to_dict()
                        log_dict['id'] = log.id
                        direct_data.append(log_dict)
                    
                    st.write(f"📊 Logs directs trouvés: {len(direct_data)}")
                    if direct_data:
                        st.success("✅ Accès direct à la collection fonctionne!")
                        for log in direct_data:
                            st.json(log)
                    else:
                        st.error("❌ Même l'accès direct échoue!")
                        
                except Exception as e:
                    st.error(f"❌ Erreur accès direct: {e}")
                    
        except Exception as e:
            st.error(f"❌ Erreur get_logs_data: {e}")
            st.write("Stack trace:", str(e))
            
    # Test des collections disponibles
    st.subheader("📋 Collections disponibles")
    if st.button("🔍 Lister collections"):
        try:
            collections = firebase_config.db.collections()
            collection_names = [col.id for col in collections]
            st.success(f"📋 Collections: {', '.join(collection_names)}")
        except Exception as e:
            st.error(f"❌ Erreur collections: {e}")

except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.info("Le fichier firebase_config.py doit être dans le même répertoire que ce script")
    
except Exception as e:
    st.error(f"❌ Erreur générale: {e}")
    st.write("Stack trace:", str(e))
