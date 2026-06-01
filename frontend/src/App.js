import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { Layout } from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Visits from "./pages/Visits";
import POCs from "./pages/POCs";
import FollowUps from "./pages/FollowUps";
import Pipeline from "./pages/Pipeline";
import Products from "./pages/Products";
import Bills from "./pages/Bills";
import Performance from "./pages/Performance";
import Employees from "./pages/Employees";
import Reports from "./pages/Reports";

import "./App.css";

function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/visits" element={<Visits />} />
              <Route path="/pocs" element={<POCs />} />
              <Route path="/followups" element={<FollowUps />} />
              <Route path="/pipeline" element={<Pipeline />} />
              <Route path="/products" element={<Products />} />
              <Route path="/bills" element={<Bills />} />
              <Route path="/performance" element={<ProtectedRoute allow={["ceo","admin","sales_manager"]}><Performance /></ProtectedRoute>} />
              <Route path="/employees" element={<ProtectedRoute allow={["ceo","admin","sales_manager"]}><Employees /></ProtectedRoute>} />
              <Route path="/reports" element={<Reports />} />
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;
