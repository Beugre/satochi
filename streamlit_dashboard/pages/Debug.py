#!/usr/bin/env python3
"""
🔍 PAGE DEBUG - TEST FIREBASE
Debug et test de la connexion Firebase
"""

import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Debug - Satochi Bot",
    page_icon="🔍",
    layout="wide"
)

try:
    from firebase_config import StreamlitFirebaseConfig
except ImportError as e:
    st.error(f"❌ Erreur import firebase_config: {e}")
    st.stop()

class DebugPage:
    """Page de debug Firebase"""
    
    def __init__(self):
        self.firebase_config = None
    
    def run(self):
        """Page de debug"""
        
        st.title("🔍 Debug Firebase - Test Direct")
        st.markdown("### 🛠️ Diagnostic des logs Firebase")
        st.markdown("---")
        
        # Test d'initialisation Firebase
        self._test_firebase_init()
        
        if self.firebase_config:
            # Tests des collections
            self._test_collections()
            
            # Test spécifique des logs
            self._test_logs_data()
            
            # Test direct de la collection
            self._test_direct_collection()
    
    def _test_firebase_init(self):
        """Test d'initialisation Firebase"""
        st.subheader("🔥 Test Initialisation Firebase")
        
        try:
            self.firebase_config = StreamlitFirebaseConfig()
            st.success("✅ Import firebase_config réussi!")
            st.success("✅ Initialisation Firebase réussie!")
            
        except Exception as e:
            st.error(f"❌ Erreur initialisation Firebase: {e}")
            st.stop()
    
    def _test_collections(self):
        """Test des collections disponibles"""
        st.subheader("📋 Collections disponibles")
        
        if st.button("🔍 Lister toutes les collections"):
            try:
                collections = self.firebase_config.db.collections()
                collection_names = [col.id for col in collections]
                st.success(f"📋 Collections trouvées: {', '.join(collection_names)}")
                
                # Afficher des détails pour chaque collection
                for name in collection_names:
                    with st.expander(f"Collection: {name}"):
                        try:
                            col_ref = self.firebase_config.db.collection(name)
                            docs = col_ref.limit(2).stream()
                            
                            doc_count = 0
                            for doc in docs:
                                doc_count += 1
                                st.write(f"**Document {doc_count}:**")
                                st.json(doc.to_dict())
                            
                            if doc_count == 0:
                                st.info("Collection vide")
                                
                        except Exception as e:
                            st.error(f"Erreur accès {name}: {e}")
                            
            except Exception as e:
                st.error(f"❌ Erreur listage collections: {e}")
    
    def _test_logs_data(self):
        """Test de la méthode get_logs_data"""
        st.subheader("📋 Test get_logs_data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            limit = st.selectbox("Limite", [5, 10, 20, 50], index=0)
        
        with col2:
            level = st.selectbox("Niveau", ["ALL", "INFO", "ERROR", "WARNING", "DEBUG"], index=0)
        
        if st.button("🔍 Tester get_logs_data"):
            try:
                st.info(f"🔍 Test avec niveau='{level}' et limite={limit}")
                
                logs_data = self.firebase_config.get_logs_data(level=level, limit=limit)
                st.write(f"📊 Nombre de logs récupérés: {len(logs_data)}")
                
                if logs_data:
                    st.success("✅ Logs trouvés!")
                    
                    # Afficher un résumé
                    st.write("**Résumé des logs:**")
                    for i, log in enumerate(logs_data[:3], 1):
                        with st.expander(f"Log {i}: {log.get('message', 'Sans message')[:50]}..."):
                            st.json(log)
                    
                    # Créer un DataFrame pour analyse
                    try:
                        df = pd.DataFrame(logs_data)
                        st.write("**Colonnes disponibles:**", list(df.columns))
                        
                        if 'timestamp' in df.columns:
                            st.write("**Exemple timestamps:**")
                            for ts in df['timestamp'].head(3):
                                st.write(f"- {ts} (type: {type(ts)})")
                        
                        if 'level' in df.columns:
                            level_counts = df['level'].value_counts()
                            st.write("**Distribution par niveau:**")
                            st.dataframe(level_counts)
                            
                    except Exception as e:
                        st.warning(f"Erreur analyse DataFrame: {e}")
                
                else:
                    st.warning("⚠️ Aucun log récupéré par get_logs_data")
                    
                    # Debug additionnel : essayer sans filtre
                    st.info("🔍 Test sans filtre de niveau...")
                    try:
                        logs_ref = self.firebase_config.db.collection('rsi_scalping_logs')
                        raw_logs = logs_ref.limit(3).stream()
                        
                        raw_data = []
                        for log in raw_logs:
                            log_dict = log.to_dict()
                            raw_data.append(log_dict)
                        
                        st.write(f"📋 Logs bruts trouvés: {len(raw_data)}")
                        if raw_data:
                            st.write("**Premier log brut:**")
                            st.json(raw_data[0])
                            
                            # Vérifier les niveaux disponibles
                            levels = [log.get('level', 'NO_LEVEL') for log in raw_data]
                            st.write(f"**Niveaux dans les logs bruts:** {levels}")
                        
                    except Exception as e2:
                        st.error(f"Erreur test brut: {e2}")
                    
            except Exception as e:
                st.error(f"❌ Erreur get_logs_data: {e}")
                st.write("**Stack trace:**", str(e))
    
    def _test_direct_collection(self):
        """Test direct de la collection rsi_scalping_logs"""
        st.subheader("🔍 Test direct collection rsi_scalping_logs")
        
        if st.button("🔍 Accès direct à la collection"):
            try:
                logs_ref = self.firebase_config.db.collection('rsi_scalping_logs')
                
                # Compter tous les documents
                st.info("🔄 Comptage des documents...")
                
                # Récupérer des échantillons
                direct_logs = logs_ref.limit(5).stream()
                
                direct_data = []
                for log in direct_logs:
                    log_dict = log.to_dict()
                    log_dict['id'] = log.id
                    direct_data.append(log_dict)
                
                st.write(f"📊 Échantillons récupérés: {len(direct_data)}")
                
                if direct_data:
                    st.success("✅ Accès direct à la collection fonctionne!")
                    
                    for i, log in enumerate(direct_data, 1):
                        with st.expander(f"Log direct {i}"):
                            st.json(log)
                    
                    # Test de conversion des timestamps
                    st.write("**Test conversion timestamps:**")
                    for log in direct_data[:2]:
                        if 'timestamp' in log:
                            original_ts = log['timestamp']
                            st.write(f"Original: {original_ts} (type: {type(original_ts)})")
                            
                            try:
                                if hasattr(original_ts, 'isoformat'):
                                    converted = original_ts.isoformat()
                                    st.write(f"Converti: {converted}")
                                else:
                                    st.write(f"String: {str(original_ts)}")
                            except Exception as e:
                                st.error(f"Erreur conversion: {e}")
                
                else:
                    st.error("❌ Aucun document trouvé dans la collection!")
                    
            except Exception as e:
                st.error(f"❌ Erreur accès direct: {e}")
                st.write("**Stack trace:**", str(e))

# Lancement de la page
page = DebugPage()
page.run()
