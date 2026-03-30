'use client';

import { useState, useEffect } from 'react';
import { ChevronDown, Cpu } from 'lucide-react';

interface Model {
  id: string;
  name: string;
  family: string;
  parameters: string;
  fine_tunable: boolean;
}

export function ModelSelector() {
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>('');
  const [isOpen, setIsOpen] = useState(false);

  useEffect(() => {
    fetch('http://localhost:8000/api/models')
      .then(res => res.json())
      .then(data => {
        setModels(data);
        if (data.length > 0) {
          setSelectedModel(data[0].id);
        }
      })
      .catch(console.error);
  }, []);

  const selectedModelData = models.find(m => m.id === selectedModel);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-gray-700 rounded-lg hover:bg-gray-600 transition-colors"
      >
        <Cpu size={18} className="text-blue-400" />
        <span className="text-sm">
          {selectedModelData?.name || 'Select Model'}
        </span>
        <ChevronDown size={16} className={`transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-gray-800 rounded-lg shadow-xl border border-gray-700 z-50">
          <div className="p-3 border-b border-gray-700">
            <h3 className="text-sm font-semibold text-gray-300">Available Models</h3>
          </div>
          <div className="max-h-96 overflow-y-auto">
            {models.map(model => (
              <button
                key={model.id}
                onClick={() => {
                  setSelectedModel(model.id);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-3 text-left hover:bg-gray-700 transition-colors flex items-center justify-between ${
                  selectedModel === model.id ? 'bg-blue-900/30 border-l-2 border-blue-400' : ''
                }`}
              >
                <div>
                  <div className="font-medium text-sm">{model.name}</div>
                  <div className="text-xs text-gray-400">
                    {model.family} • {model.parameters}
                  </div>
                </div>
                {model.fine_tunable && (
                  <span className="text-xs bg-green-900/50 text-green-400 px-2 py-1 rounded">
                    Fine-tunable
                  </span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
