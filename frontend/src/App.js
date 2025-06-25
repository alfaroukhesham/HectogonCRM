import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Modal Component
const Modal = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md mx-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-bold">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700"
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

// Contact Form Component
const ContactForm = ({ contact, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
    company: "",
    position: "",
    address: "",
    notes: "",
    ...contact,
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (contact?.id) {
        await axios.put(`${API}/contacts/${contact.id}`, formData);
      } else {
        await axios.post(`${API}/contacts`, formData);
      }
      onSave();
    } catch (error) {
      console.error("Error saving contact:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-2 gap-4">
        <input
          type="text"
          placeholder="First Name"
          value={formData.first_name}
          onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
          required
        />
        <input
          type="text"
          placeholder="Last Name"
          value={formData.last_name}
          onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
          required
        />
      </div>
      <input
        type="email"
        placeholder="Email"
        value={formData.email}
        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
        required
      />
      <input
        type="text"
        placeholder="Phone"
        value={formData.phone}
        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
      />
      <div className="grid grid-cols-2 gap-4">
        <input
          type="text"
          placeholder="Company"
          value={formData.company}
          onChange={(e) => setFormData({ ...formData, company: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
        />
        <input
          type="text"
          placeholder="Position"
          value={formData.position}
          onChange={(e) => setFormData({ ...formData, position: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
        />
      </div>
      <input
        type="text"
        placeholder="Address"
        value={formData.address}
        onChange={(e) => setFormData({ ...formData, address: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
      />
      <textarea
        placeholder="Notes"
        value={formData.notes}
        onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2 h-20"
      />
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          {contact?.id ? "Update" : "Create"} Contact
        </button>
      </div>
    </form>
  );
};

// Deal Form Component
const DealForm = ({ deal, contacts, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    title: "",
    contact_id: "",
    value: "",
    stage: "Lead",
    probability: 50,
    expected_close_date: "",
    description: "",
    ...deal,
  });

  const stages = ["Lead", "Qualified", "Proposal", "Negotiation", "Closed Won", "Closed Lost"];

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        value: parseFloat(formData.value),
        expected_close_date: formData.expected_close_date || null,
      };
      
      if (deal?.id) {
        await axios.put(`${API}/deals/${deal.id}`, submitData);
      } else {
        await axios.post(`${API}/deals`, submitData);
      }
      onSave();
    } catch (error) {
      console.error("Error saving deal:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <input
        type="text"
        placeholder="Deal Title"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
        required
      />
      <select
        value={formData.contact_id}
        onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
        required
      >
        <option value="">Select Contact</option>
        {contacts.map((contact) => (
          <option key={contact.id} value={contact.id}>
            {contact.first_name} {contact.last_name} - {contact.company}
          </option>
        ))}
      </select>
      <div className="grid grid-cols-2 gap-4">
        <input
          type="number"
          placeholder="Deal Value"
          value={formData.value}
          onChange={(e) => setFormData({ ...formData, value: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
          required
        />
        <select
          value={formData.stage}
          onChange={(e) => setFormData({ ...formData, stage: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
        >
          {stages.map((stage) => (
            <option key={stage} value={stage}>
              {stage}
            </option>
          ))}
        </select>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <input
          type="number"
          min="0"
          max="100"
          placeholder="Probability %"
          value={formData.probability}
          onChange={(e) => setFormData({ ...formData, probability: parseInt(e.target.value) })}
          className="border border-gray-300 rounded px-3 py-2"
        />
        <input
          type="date"
          placeholder="Expected Close Date"
          value={formData.expected_close_date}
          onChange={(e) => setFormData({ ...formData, expected_close_date: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
        />
      </div>
      <textarea
        placeholder="Description"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2 h-20"
      />
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          {deal?.id ? "Update" : "Create"} Deal
        </button>
      </div>
    </form>
  );
};

// Activity Form Component
const ActivityForm = ({ activity, contacts, onSave, onCancel }) => {
  const [formData, setFormData] = useState({
    contact_id: "",
    type: "Note",
    title: "",
    description: "",
    due_date: "",
    priority: "Medium",
    ...activity,
  });

  const types = ["Call", "Email", "Meeting", "Note", "Task"];
  const priorities = ["Low", "Medium", "High"];

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const submitData = {
        ...formData,
        due_date: formData.due_date || null,
      };
      
      if (activity?.id) {
        await axios.put(`${API}/activities/${activity.id}`, submitData);
      } else {
        await axios.post(`${API}/activities`, submitData);
      }
      onSave();
    } catch (error) {
      console.error("Error saving activity:", error);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <select
        value={formData.contact_id}
        onChange={(e) => setFormData({ ...formData, contact_id: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
        required
      >
        <option value="">Select Contact</option>
        {contacts.map((contact) => (
          <option key={contact.id} value={contact.id}>
            {contact.first_name} {contact.last_name} - {contact.company}
          </option>
        ))}
      </select>
      <div className="grid grid-cols-2 gap-4">
        <select
          value={formData.type}
          onChange={(e) => setFormData({ ...formData, type: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
        >
          {types.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
        <select
          value={formData.priority}
          onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
          className="border border-gray-300 rounded px-3 py-2"
        >
          {priorities.map((priority) => (
            <option key={priority} value={priority}>
              {priority}
            </option>
          ))}
        </select>
      </div>
      <input
        type="text"
        placeholder="Activity Title"
        value={formData.title}
        onChange={(e) => setFormData({ ...formData, title: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
        required
      />
      <input
        type="datetime-local"
        placeholder="Due Date"
        value={formData.due_date}
        onChange={(e) => setFormData({ ...formData, due_date: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2"
      />
      <textarea
        placeholder="Description"
        value={formData.description}
        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
        className="w-full border border-gray-300 rounded px-3 py-2 h-20"
      />
      <div className="flex justify-end space-x-3">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-gray-600 border border-gray-300 rounded hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700"
        >
          {activity?.id ? "Update" : "Create"} Activity
        </button>
      </div>
    </form>
  );
};

// Main App Component
function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [contacts, setContacts] = useState([]);
  const [deals, setDeals] = useState([]);
  const [activities, setActivities] = useState([]);
  const [dashboardStats, setDashboardStats] = useState({});
  const [searchTerm, setSearchTerm] = useState("");
  
  // Modal states
  const [showContactModal, setShowContactModal] = useState(false);
  const [showDealModal, setShowDealModal] = useState(false);
  const [showActivityModal, setShowActivityModal] = useState(false);
  const [editingContact, setEditingContact] = useState(null);
  const [editingDeal, setEditingDeal] = useState(null);
  const [editingActivity, setEditingActivity] = useState(null);

  // Load data
  const loadContacts = async () => {
    try {
      const response = await axios.get(`${API}/contacts`, {
        params: searchTerm ? { search: searchTerm } : {}
      });
      setContacts(response.data);
    } catch (error) {
      console.error("Error loading contacts:", error);
    }
  };

  const loadDeals = async () => {
    try {
      const response = await axios.get(`${API}/deals`);
      setDeals(response.data);
    } catch (error) {
      console.error("Error loading deals:", error);
    }
  };

  const loadActivities = async () => {
    try {
      const response = await axios.get(`${API}/activities`);
      setActivities(response.data);
    } catch (error) {
      console.error("Error loading activities:", error);
    }
  };

  const loadDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setDashboardStats(response.data);
    } catch (error) {
      console.error("Error loading dashboard stats:", error);
    }
  };

  useEffect(() => {
    loadContacts();
    loadDeals();
    loadActivities();
    loadDashboardStats();
  }, []);

  useEffect(() => {
    loadContacts();
  }, [searchTerm]);

  const handleContactSave = () => {
    setShowContactModal(false);
    setEditingContact(null);
    loadContacts();
    loadDashboardStats();
  };

  const handleDealSave = () => {
    setShowDealModal(false);
    setEditingDeal(null);
    loadDeals();
    loadDashboardStats();
  };

  const handleActivitySave = () => {
    setShowActivityModal(false);
    setEditingActivity(null);
    loadActivities();
  };

  const deleteContact = async (id) => {
    if (window.confirm("Are you sure you want to delete this contact?")) {
      try {
        await axios.delete(`${API}/contacts/${id}`);
        loadContacts();
        loadDashboardStats();
      } catch (error) {
        console.error("Error deleting contact:", error);
      }
    }
  };

  const deleteDeal = async (id) => {
    if (window.confirm("Are you sure you want to delete this deal?")) {
      try {
        await axios.delete(`${API}/deals/${id}`);
        loadDeals();
        loadDashboardStats();
      } catch (error) {
        console.error("Error deleting deal:", error);
      }
    }
  };

  const getContactName = (contactId) => {
    const contact = contacts.find(c => c.id === contactId);
    return contact ? `${contact.first_name} ${contact.last_name}` : "Unknown";
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStageColor = (stage) => {
    const colors = {
      "Lead": "bg-gray-100 text-gray-800",
      "Qualified": "bg-blue-100 text-blue-800",
      "Proposal": "bg-yellow-100 text-yellow-800",
      "Negotiation": "bg-orange-100 text-orange-800",
      "Closed Won": "bg-green-100 text-green-800",
      "Closed Lost": "bg-red-100 text-red-800"
    };
    return colors[stage] || "bg-gray-100 text-gray-800";
  };

  const getPriorityColor = (priority) => {
    const colors = {
      "Low": "bg-green-100 text-green-800",
      "Medium": "bg-yellow-100 text-yellow-800",
      "High": "bg-red-100 text-red-800"
    };
    return colors[priority] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-gray-900">CRM System</h1>
            </div>
            <nav className="flex space-x-8">
              {["dashboard", "contacts", "deals", "activities"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`capitalize px-3 py-2 rounded-md text-sm font-medium ${
                    activeTab === tab
                      ? "bg-blue-100 text-blue-700"
                      : "text-gray-500 hover:text-gray-700"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        {/* Dashboard */}
        {activeTab === "dashboard" && (
          <div className="px-4 py-6 sm:px-0">
            <h2 className="text-2xl font-bold mb-6">Dashboard</h2>
            
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-md flex items-center justify-center">
                        <span className="text-blue-600 font-bold">👥</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total Contacts
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {dashboardStats.total_contacts || 0}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-green-100 rounded-md flex items-center justify-center">
                        <span className="text-green-600 font-bold">📊</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total Deals
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {dashboardStats.total_deals || 0}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-purple-100 rounded-md flex items-center justify-center">
                        <span className="text-purple-600 font-bold">💰</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Total Revenue
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {formatCurrency(dashboardStats.total_revenue || 0)}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white overflow-hidden shadow rounded-lg">
                <div className="p-5">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-yellow-100 rounded-md flex items-center justify-center">
                        <span className="text-yellow-600 font-bold">🚀</span>
                      </div>
                    </div>
                    <div className="ml-5 w-0 flex-1">
                      <dl>
                        <dt className="text-sm font-medium text-gray-500 truncate">
                          Pipeline Value
                        </dt>
                        <dd className="text-lg font-medium text-gray-900">
                          {formatCurrency(dashboardStats.pipeline_value || 0)}
                        </dd>
                      </dl>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Deals by Stage */}
            <div className="bg-white shadow rounded-lg p-6">
              <h3 className="text-lg font-medium mb-4">Deals by Stage</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                {Object.entries(dashboardStats.deals_by_stage || {}).map(([stage, count]) => (
                  <div key={stage} className="text-center">
                    <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm ${getStageColor(stage)}`}>
                      {stage}
                    </div>
                    <div className="mt-2 text-2xl font-bold text-gray-900">{count}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Contacts */}
        {activeTab === "contacts" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Contacts</h2>
              <button
                onClick={() => setShowContactModal(true)}
                className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700"
              >
                Add Contact
              </button>
            </div>

            {/* Search */}
            <div className="mb-6">
              <input
                type="text"
                placeholder="Search contacts..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full max-w-md border border-gray-300 rounded-md px-3 py-2"
              />
            </div>

            {/* Contacts List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {contacts.map((contact) => (
                  <li key={contact.id}>
                    <div className="px-4 py-4 flex items-center justify-between">
                      <div className="flex items-center">
                        <div className="flex-shrink-0 h-10 w-10">
                          <div className="h-10 w-10 rounded-full bg-blue-100 flex items-center justify-center">
                            <span className="text-blue-600 font-medium">
                              {contact.first_name[0]}{contact.last_name[0]}
                            </span>
                          </div>
                        </div>
                        <div className="ml-4">
                          <div className="text-sm font-medium text-gray-900">
                            {contact.first_name} {contact.last_name}
                          </div>
                          <div className="text-sm text-gray-500">
                            {contact.email} • {contact.company}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            setEditingContact(contact);
                            setShowContactModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deleteContact(contact.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Deals */}
        {activeTab === "deals" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Deals</h2>
              <button
                onClick={() => setShowDealModal(true)}
                className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700"
              >
                Add Deal
              </button>
            </div>

            {/* Deals List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {deals.map((deal) => (
                  <li key={deal.id}>
                    <div className="px-4 py-4 flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {deal.title}
                        </div>
                        <div className="text-sm text-gray-500">
                          {getContactName(deal.contact_id)} • {formatCurrency(deal.value)}
                        </div>
                        <div className="mt-1">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStageColor(deal.stage)}`}>
                            {deal.stage}
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            setEditingDeal(deal);
                            setShowDealModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => deleteDeal(deal.id)}
                          className="text-red-600 hover:text-red-900"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {/* Activities */}
        {activeTab === "activities" && (
          <div className="px-4 py-6 sm:px-0">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold">Activities</h2>
              <button
                onClick={() => setShowActivityModal(true)}
                className="bg-purple-600 text-white px-4 py-2 rounded-md hover:bg-purple-700"
              >
                Add Activity
              </button>
            </div>

            {/* Activities List */}
            <div className="bg-white shadow overflow-hidden sm:rounded-md">
              <ul className="divide-y divide-gray-200">
                {activities.map((activity) => (
                  <li key={activity.id}>
                    <div className="px-4 py-4 flex items-center justify-between">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {activity.title}
                        </div>
                        <div className="text-sm text-gray-500">
                          {getContactName(activity.contact_id)} • {activity.type}
                          {activity.due_date && ` • Due: ${formatDate(activity.due_date)}`}
                        </div>
                        <div className="mt-1 flex items-center space-x-2">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(activity.priority)}`}>
                            {activity.priority}
                          </span>
                          {activity.completed && (
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                              Completed
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <button
                          onClick={() => {
                            setEditingActivity(activity);
                            setShowActivityModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-900"
                        >
                          Edit
                        </button>
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </main>

      {/* Modals */}
      <Modal
        isOpen={showContactModal}
        onClose={() => {
          setShowContactModal(false);
          setEditingContact(null);
        }}
        title={editingContact ? "Edit Contact" : "Add Contact"}
      >
        <ContactForm
          contact={editingContact}
          onSave={handleContactSave}
          onCancel={() => {
            setShowContactModal(false);
            setEditingContact(null);
          }}
        />
      </Modal>

      <Modal
        isOpen={showDealModal}
        onClose={() => {
          setShowDealModal(false);
          setEditingDeal(null);
        }}
        title={editingDeal ? "Edit Deal" : "Add Deal"}
      >
        <DealForm
          deal={editingDeal}
          contacts={contacts}
          onSave={handleDealSave}
          onCancel={() => {
            setShowDealModal(false);
            setEditingDeal(null);
          }}
        />
      </Modal>

      <Modal
        isOpen={showActivityModal}
        onClose={() => {
          setShowActivityModal(false);
          setEditingActivity(null);
        }}
        title={editingActivity ? "Edit Activity" : "Add Activity"}
      >
        <ActivityForm
          activity={editingActivity}
          contacts={contacts}
          onSave={handleActivitySave}
          onCancel={() => {
            setShowActivityModal(false);
            setEditingActivity(null);
          }}
        />
      </Modal>
    </div>
  );
}

export default App;