function AppShell({ children }) {
  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="flex">
        <nav className="w-64 bg-white border-r border-neutral-200 min-h-screen p-4">
          <div className="text-lg font-heading font-bold text-primary-600 mb-8">
            App
          </div>
          {/* Navigation will be built in build-shell step */}
        </nav>
        <main className="flex-1">
          {children}
        </main>
      </div>
    </div>
  );
}

export default AppShell;
