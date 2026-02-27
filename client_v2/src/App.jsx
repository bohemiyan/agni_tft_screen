import { useState, useEffect } from 'react'
import { getSensors, getWidgets, getScreens, getThemes, addSensor, addWidget, addScreen, addTheme } from './api'
import { Server, Activity, Monitor, LayoutTemplate, ShieldAlert } from 'lucide-react'
import EditorPane from './components/EditorPane'

function App() {
  const [activeTab, setActiveTab] = useState('sensors');
  const [activeItem, setActiveItem] = useState(null);
  const [registry, setRegistry] = useState({
    sensors: [], widgets: [], screens: [], themes: []
  });

  const loadData = async () => {
    try {
      const [sens, wid, scr, thm] = await Promise.all([
        getSensors(), getWidgets(), getScreens(), getThemes()
      ]);
      setRegistry({ sensors: sens, widgets: wid, screens: scr, themes: thm });
    } catch (e) {
      console.error("Failed to load registry from PyServer", e);
    }
  };

  useEffect(() => { 
     loadData(); 
     setActiveItem(null); // Clear editor on tab switch
  }, [activeTab]);

  useEffect(() => {
     let interval;
     const fetchCanvas = async () => {
        try {
           const res = await fetch('http://localhost:8888/api/v1/hardware/lcd/screen');
           const blob = await res.blob();
           const arrayBuffer = await blob.arrayBuffer();
           const bytes = new Uint8Array(arrayBuffer);
           
           const canvas = document.getElementById('tft-canvas');
           if (!canvas) return;
           const ctx = canvas.getContext('2d');
           
           // RGB565 to RGBA conversion
           const imgData = ctx.createImageData(320, 170);
           for (let i = 0, j = 0; i < bytes.length; i += 2, j += 4) {
               const rgb565 = (bytes[i] << 8) | bytes[i + 1];
               const r = ((rgb565 >> 11) & 0x1F) * 255 / 31;
               const g = ((rgb565 >> 5) & 0x3F) * 255 / 63;
               const b = (rgb565 & 0x1F) * 255 / 31;
               imgData.data[j] = r;
               imgData.data[j + 1] = g;
               imgData.data[j + 2] = b;
               imgData.data[j + 3] = 255; // Alpha
           }
           ctx.putImageData(imgData, 0, 0);
        } catch (e) {
           // Silently fail if server is down or screen hasn't drawn
        }
     };

     interval = setInterval(fetchCanvas, 500); // 2fps polling config
     return () => clearInterval(interval);
  }, []);

  const renderIcon = (type) => {
    if (activeTab === 'sensors') return <Activity className="w-5 h-5" />;
    if (activeTab === 'widgets') return <LayoutTemplate className="w-5 h-5" />;
    if (activeTab === 'screens') return <Monitor className="w-5 h-5" />;
    return <Server className="w-5 h-5" />;
  };

  return (
    <div className="flex h-screen w-full bg-gray-950 text-gray-100 font-sans selection:bg-orange-500/30">
      
      {/* LEFT PANE: TFT Live Preview + Editor */}
      <div className="w-1/2 flex flex-col border-r border-gray-800">
        
        {/* Top: LCD Screen Preview */}
        <div className="bg-gray-900 border-b border-gray-800 p-8 flex flex-col items-center justify-center min-h-[300px]">
          <h2 className="text-gray-400 text-sm mb-4 tracking-widest uppercase font-semibold flex items-center gap-2">
            <Monitor className="w-4 h-4 text-emerald-500" /> Live TFT Preview
          </h2>
          <div className="relative border-8 border-gray-800 rounded-xl overflow-hidden bg-black shadow-2xl flex items-center justify-center p-1" style={{ width: '335px', height: '185px' }}>
             <canvas id="tft-canvas" width="320" height="170" className="w-[320px] h-[170px] bg-black rounded shadow-inner" />
          </div>
        </div>

        {/* Bottom: Component Editor */}
        <div className="flex-1 overflow-auto bg-gray-950 p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-orange-400 to-rose-400 border-b border-gray-800 pb-2 w-full flex justify-between">
              {activeItem ? (activeItem.id ? `Editing ${activeItem.name}` : 'Creating New Component') : 'Component Editor'}
              {!activeItem && (
                 <button 
                    onClick={() => {
                        // Scaffold an empty template based on active tab
                        const template = { name: `New ${activeTab.slice(0, -1)}` };
                        if (activeTab === 'sensors') template.type = "cpu_usage";
                        if (activeTab === 'widgets') { template.type = "text"; template.rect = {x:0, y:0, width:100, height:20}; template.properties = {}; }
                        if (activeTab === 'screens') { template.background = "#000000"; template.widget_ids = []; }
                        if (activeTab === 'themes') { template.orientation = "landscape"; template.screen_ids = []; template.rotation_interval = 60000; }
                        setActiveItem(template);
                    }}
                    className="px-4 py-1.5 -translate-y-1 bg-gray-800 hover:bg-gray-700 text-sm font-semibold rounded-lg transition-colors border border-gray-700 hover:border-gray-500 text-white"
                 >
                    + Create New
                 </button>
              )}
            </h2>
          </div>
          
          {activeItem ? (
             <EditorPane 
                item={activeItem} 
                tab={activeTab} 
                onSave={async (data) => {
                   try {
                     if (activeTab === 'sensors') await addSensor(data);
                     if (activeTab === 'widgets') await addWidget(data);
                     if (activeTab === 'screens') await addScreen(data);
                     if (activeTab === 'themes') await addTheme(data);
                     setActiveItem(null);
                     loadData();
                   } catch (e) {
                     alert("Failed to save to PyServer");
                   }
                }}
                onCancel={() => setActiveItem(null)} 
             />
          ) : (
             <div className="flex flex-col items-center justify-center h-48 text-gray-600 border border-dashed border-gray-800 rounded-xl bg-gray-900/30">
                <div className="p-4 rounded-full bg-gray-900 mb-2">
                   <ShieldAlert className="w-6 h-6 opacity-50" />
                </div>
                Select an item from the registry tabs to edit
             </div>
          )}
        </div>
      </div>

      {/* RIGHT PANE: Modular Registry Explorer */}
      <div className="w-1/2 flex flex-col bg-gray-900/20">
        <div className="p-6 border-b border-gray-800 bg-gray-900/50">
           <div className="flex justify-between items-center">
             <h1 className="text-2xl font-black text-white flex items-center gap-3 tracking-tight">
                <span className="bg-gradient-to-br from-orange-500 to-rose-600 text-white p-1.5 rounded-lg text-sm shadow-lg shadow-orange-900/20">AGNI</span> 
                Modular Registry
             </h1>
             <div className="text-xs text-green-400 flex items-center gap-1.5 bg-green-400/10 px-2.5 py-1 rounded-full border border-green-400/20">
                <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
                PyServer Connected
             </div>
           </div>
           <p className="text-sm text-gray-400 mt-2 font-medium">Manage isolated Hardware Sensors, Display Widgets, and Theme pools.</p>
        </div>
        
        {/* Navigation Tabs */}
        <div className="flex border-b border-gray-800 pt-4 px-6 gap-8 text-sm font-semibold selection:bg-transparent">
           {['sensors', 'widgets', 'screens', 'themes'].map(tab => (
             <button 
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-3 transition-colors capitalize ${activeTab === tab ? 'text-orange-400 border-b-2 border-orange-400' : 'text-gray-500 hover:text-gray-300'}`}
             >
               {tab} <span className="text-xs opacity-50 ml-1 bg-gray-800 px-1.5 py-0.5 rounded-md">{registry[tab].length}</span>
             </button>
           ))}
        </div>

        {/* List Content Area */}
        <div className="flex-1 overflow-auto p-6 space-y-3">
            {registry[activeTab].map(item => (
               <div 
                  key={item.id} 
                  onClick={() => setActiveItem(item)}
                  className={`group flex justify-between items-center p-4 rounded-xl border cursor-pointer transition-all hover:shadow-lg ${activeItem?.id === item.id ? 'bg-gray-800 border-orange-500/50 shadow-orange-900/10' : 'bg-gray-900 border-gray-800 hover:border-gray-700 hover:bg-gray-800/80'}`}
               >
                  <div className="flex items-center gap-4">
                     <div className={`w-10 h-10 rounded-lg flex items-center justify-center border transition-colors ${
                        activeTab === 'sensors' ? 'bg-blue-900/20 border-blue-900/40 text-blue-400 group-hover:bg-blue-900/40' :
                        activeTab === 'widgets' ? 'bg-purple-900/20 border-purple-900/40 text-purple-400 group-hover:bg-purple-900/40' :
                        activeTab === 'screens' ? 'bg-emerald-900/20 border-emerald-900/40 text-emerald-400 group-hover:bg-emerald-900/40' :
                        'bg-rose-900/20 border-rose-900/40 text-rose-400 group-hover:bg-rose-900/40'
                     }`}>
                        {renderIcon(item.type)}
                     </div>
                     <div>
                        <h3 className="font-bold text-gray-200">{item.name}</h3>
                        <p className="text-xs text-gray-500 max-w-[200px] truncate">
                           ID: {item.id} • {item.type ? `Type: ${item.type}` : `${item.widget_ids ? item.widget_ids.length : 0} items`}
                        </p>
                     </div>
                  </div>
                  {item.protected && (
                    <span className="bg-red-950/40 text-red-400 text-[10px] uppercase font-bold px-2.5 py-1 rounded-md border border-red-900/50 flex items-center gap-1.5">
                       <ShieldAlert className="w-3 h-3" /> Protected
                    </span>
                  )}
               </div>
            ))}
            
            {registry[activeTab].length === 0 && (
               <div className="text-center text-gray-600 py-10">No {activeTab} found in registry.</div>
            )}
        </div>
      </div>
    </div>
  )
}

export default App
