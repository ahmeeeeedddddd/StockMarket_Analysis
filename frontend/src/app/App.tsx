import { BrowserRouter, Routes, Route } from 'react-router';
import { Navbar } from './components/Navbar';
import { Dashboard } from './pages/Dashboard';
import { StockDetail } from './pages/StockDetail';
import { AlertsHistory } from './pages/AlertsHistory';
import { DeepDive } from './pages/DeepDive';

export default function App() {
  return (
    <BrowserRouter>
      <div className="h-screen flex flex-col bg-background">
        <Navbar />
        <div className="flex-1 min-h-0">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/stock/:symbol" element={<StockDetail />} />
            <Route path="/alerts" element={<AlertsHistory />} />
            <Route path="/deep-dive/:symbol" element={<DeepDive />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}