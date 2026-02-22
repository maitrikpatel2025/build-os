import { Routes, Route } from 'react-router-dom';
import AppShell from './shell/AppShell';

function App() {
  return (
    <AppShell>
      <Routes>
        <Route path="/" element={<div className="p-6"><h1 className="text-2xl font-heading font-bold">Welcome</h1></div>} />
        {/* Section routes will be added by build-section commands */}
      </Routes>
    </AppShell>
  );
}

export default App;
