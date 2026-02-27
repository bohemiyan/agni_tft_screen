import { useState, useEffect } from 'react'

export default function EditorPane({ item, tab, onSave, onCancel }) {
  const [formData, setFormData] = useState({});
  const [isCloning, setIsCloning] = useState(false);

  useEffect(() => {
    if (item) {
       setFormData(JSON.parse(JSON.stringify(item)));
       setIsCloning(false);
    }
  }, [item]);

  if (!item) return null;

  const isProtected = item.protected && !isCloning;

  const handleSave = () => {
    // If cloning a protected item, strip its ID so the backend generates a new one
    const submitData = { ...formData };
    if (isCloning) {
      delete submitData.id;
      delete submitData.protected; // Ensure the new clone is editable
    }
    onSave(submitData);
  };

  const handleClone = () => {
    setIsCloning(true);
    setFormData({ ...formData, name: `${formData.name} (Copy)` });
  };

  return (
    <div className="flex flex-col h-full">
      
      {isProtected && (
        <div className="bg-red-950/30 border border-red-900 text-red-400 p-4 rounded-lg mb-6 flex items-start gap-3">
          <svg className="w-5 h-5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>
          <div>
            <h4 className="font-bold text-sm">System Protected Item</h4>
            <p className="text-xs text-red-400/80 mt-1">This is a core system component required for OOTB operation. It cannot be modified or deleted. To make changes, you must clone it as a new unprotected instance.</p>
          </div>
        </div>
      )}

      {isCloning && (
        <div className="bg-blue-900/20 border border-blue-800 text-blue-300 p-4 rounded-lg mb-6 flex items-start gap-3">
           <svg className="w-5 h-5 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" /></svg>
           <div>
             <h4 className="font-bold text-sm">Cloning Instance</h4>
             <p className="text-xs text-blue-300/80 mt-1">You are creating a new editable instance based on the original data. Please provide a new unique name.</p>
           </div>
        </div>
      )}

      <div className="space-y-4 flex-1 overflow-auto">
        <label className="block">
           <span className="text-xs font-bold text-gray-500 uppercase tracking-widest pl-1">Configuration Name</span>
           <input 
              type="text" 
              className={`mt-1 block w-full rounded-md bg-gray-900 border p-3 text-sm focus:ring-2 focus:outline-none transition-colors ${isProtected ? 'border-gray-800 text-gray-500 cursor-not-allowed' : 'border-gray-700 text-white focus:border-orange-500 focus:ring-orange-500/20'}`}
              value={formData.name || ''}
              onChange={e => setFormData({...formData, name: e.target.value})}
              disabled={isProtected}
           />
        </label>
        
        <label className="block">
           <span className="text-xs font-bold text-gray-500 uppercase tracking-widest pl-1">ID (Auto-Generated)</span>
           <input 
              type="text" 
              className="mt-1 block w-full rounded-md bg-gray-900 border border-gray-800 p-3 text-sm text-gray-600 font-mono cursor-not-allowed"
              value={isCloning ? 'WILL BE GENERATED ON SAVE' : formData.id || 'NEW'}
              disabled
           />
        </label>

        <label className="block">
           <span className="text-xs font-bold text-gray-500 uppercase tracking-widest pl-1">JSON Payload Data</span>
           <textarea 
              rows={8}
              className={`mt-1 block w-full rounded-md bg-gray-950 font-mono border p-3 text-xs focus:ring-2 focus:outline-none transition-colors align-top ${isProtected ? 'border-gray-800 text-gray-600 cursor-not-allowed' : 'border-gray-700 text-green-400 focus:border-orange-500 focus:ring-orange-500/20'}`}
              value={JSON.stringify(formData, null, 2)}
              onChange={e => {
                 try {
                     const parsed = JSON.parse(e.target.value);
                     setFormData(parsed);
                 } catch(err) {
                     // ignore parse errors while typing
                 }
              }}
              disabled={isProtected}
           />
        </label>
      </div>

      <div className="mt-8 pt-4 border-t border-gray-800 flex gap-3">
         {isProtected ? (
           <button onClick={handleClone} className="flex-1 py-3 bg-blue-600 hover:bg-blue-500 text-white font-bold rounded-lg transition-colors">
              Clone & Edit
           </button>
         ) : (
           <button onClick={handleSave} className="flex-1 py-3 bg-green-600 hover:bg-green-500 text-white font-bold rounded-lg transition-colors">
              Save {tab.replace(/s$/, '')} Registry
           </button>
         )}
         <button onClick={onCancel} className="px-6 py-3 bg-gray-800 hover:bg-gray-700 text-white font-bold rounded-lg transition-colors">
            Cancel
         </button>
      </div>
    </div>
  )
}
