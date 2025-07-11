import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout, ErrorBoundary } from './components';
import { AuthProvider } from './hooks/useAuth';
import { OrganizationProvider } from './hooks/useOrganization';
import ProtectedRoute from './components/ProtectedRoute';
import { Dashboard, Contacts, Deals, Activities } from './pages';
import Login from './pages/Login';
import Register from './pages/Register';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';
import { useTheme } from './hooks/useTheme';
import { MembershipRole } from './types';
import NotFound from './pages/NotFound';
import './App.css';

// Lazy load organization management pages
const Organizations = React.lazy(() => import('./pages/Organizations'));
const OrganizationSettings = React.lazy(() => import('./pages/OrganizationSettings'));
const TeamMembers = React.lazy(() => import('./pages/TeamMembers'));
const Invitations = React.lazy(() => import('./pages/Invitations'));

const App: React.FC = () => {
  // Initialize theme
  useTheme();

  return (
    <ErrorBoundary>
      <AuthProvider>
        <OrganizationProvider>
          <Router>
            <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-300">
              <Routes>
                {/* Public routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/forgot-password" element={<ForgotPassword />} />
                <Route path="/reset-password" element={<ResetPassword />} />
                <Route path="/auth/success" element={<Navigate to="/" replace />} />

                {/* Protected routes */}
                <Route path="/*" element={
                  <ProtectedRoute>
                    <MainLayout>
                      <Routes>
                        <Route index element={<Dashboard />} />
                        
                        <Route path="contacts">
                          <Route index element={<Contacts />} />
                          <Route path=":id" element={<Contacts />} />
                        </Route>
                        
                        <Route path="deals">
                          <Route index element={<Deals />} />
                          <Route path=":id" element={<Deals />} />
                          <Route path="by-stage/:stage" element={<Deals />} />
                        </Route>
                        
                        <Route path="activities">
                          <Route index element={<Activities />} />
                          <Route path="contact/:contactId" element={<Activities />} />
                          <Route path="deal/:dealId" element={<Activities />} />
                          <Route path="type/:type" element={<Activities />} />
                        </Route>

                        {/* Organization management routes */}
                        <Route path="organizations">
                          <Route 
                            index 
                            element={
                              <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
                                <ErrorBoundary fallback={<div className="p-6 text-center text-red-600">Failed to load Organizations</div>}>
                                  <Organizations />
                                </ErrorBoundary>
                              </React.Suspense>
                            } 
                          />
                        </Route>
                        
                        <Route path="team">
                          <Route 
                            index 
                            element={
                              <ProtectedRoute requiredOrganizationRole={MembershipRole.ADMIN}>
                                <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
                                  <ErrorBoundary fallback={<div className="p-6 text-center text-red-600">Failed to load Team Members</div>}>
                                    <TeamMembers />
                                  </ErrorBoundary>
                                </React.Suspense>
                              </ProtectedRoute>
                            } 
                          />
                        </Route>
                        
                        <Route path="invitations">
                          <Route 
                            index 
                            element={
                              <ProtectedRoute requiredOrganizationRole={MembershipRole.ADMIN}>
                                <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
                                  <ErrorBoundary fallback={<div className="p-6 text-center text-red-600">Failed to load Invitations</div>}>
                                    <Invitations />
                                  </ErrorBoundary>
                                </React.Suspense>
                              </ProtectedRoute>
                            } 
                          />
                        </Route>
                        
                        <Route path="settings">
                          <Route 
                            index
                            element={
                              <ProtectedRoute requiredOrganizationRole={MembershipRole.ADMIN}>
                                <React.Suspense fallback={<div className="p-6 text-center">Loading...</div>}>
                                  <ErrorBoundary fallback={<div className="p-6 text-center text-red-600">Failed to load Settings</div>}>
                                    <OrganizationSettings />
                                  </ErrorBoundary>
                                </React.Suspense>
                              </ProtectedRoute>
                            }
                          />
                        </Route>
                        
                        <Route path="reports">
                          <Route 
                            index
                            element={<div className="p-6 text-center text-gray-500 dark:text-gray-400">Reports coming soon...</div>}
                          />
                        </Route>
                      </Routes>
                    </MainLayout>
                  </ProtectedRoute>
                } />

                {/* Catch all route */}
                <Route path="*" element={<NotFound />} />
              </Routes>
            </div>
          </Router>
        </OrganizationProvider>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App; 
