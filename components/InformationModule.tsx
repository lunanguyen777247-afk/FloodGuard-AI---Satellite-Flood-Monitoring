
import React, { useState } from 'react';
import { 
  Info, 
  Satellite, 
  CloudRain, 
  Settings, 
  Bell, 
  Mail, 
  Send, 
  CheckCircle2, 
  HelpCircle, 
  Cpu,
  History
} from 'lucide-react';

export const InformationModule: React.FC = () => {
  const [subscribed, setSubscribed] = useState(false);
  const [frequency, setFrequency] = useState('daily');
  const [contact, setContact] = useState('');

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (contact) {
      setSubscribed(true);
      setTimeout(() => setSubscribed(false), 5000);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-10 animate-in fade-in slide-in-from-bottom-6 duration-700">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row gap-6 items-start justify-between">
        <div className="space-y-2">
          <h2 className="text-3xl font-black text-white tracking-tight flex items-center gap-3">
            <Info className="w-8 h-8 text-blue-400" />
            Thông tin hệ thống
          </h2>
          <p className="text-slate-400 font-medium">Tìm hiểu về công nghệ viễn thám và cấu hình thông báo báo cáo tự động.</p>
        </div>
        
        <div className="flex gap-4 p-2 bg-slate-900/50 rounded-2xl border border-slate-800">
          <div className="px-4 py-2 text-center">
            <span className="block text-blue-400 font-black text-xl">v4.2.0</span>
            <span className="text-[10px] text-slate-500 uppercase font-bold">Phiên bản</span>
          </div>
          <div className="w-px bg-slate-800 my-2"></div>
          <div className="px-4 py-2 text-center">
            <span className="block text-green-400 font-black text-xl">Stable</span>
            <span className="text-[10px] text-slate-500 uppercase font-bold">Trạng thái</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Data & Technology */}
        <div className="lg:col-span-2 space-y-8">
          <section className="bg-slate-800/40 border border-slate-700 rounded-[2rem] p-8 backdrop-blur-sm">
            <h3 className="text-white font-bold text-lg mb-6 flex items-center gap-3">
              <Cpu className="w-5 h-5 text-blue-400" />
              Nguồn dữ liệu & Công nghệ
            </h3>
            
            <div className="space-y-6">
              <TechCard 
                icon={<Satellite className="text-blue-400" />}
                title="Sentinel-1 SAR (C-Band)"
                content="Sử dụng radar xuyên mây và mưa để xác định ranh giới vùng ngập (Flood Mask) với độ phân giải 10m. Khả năng giám sát 24/7 không phụ thuộc điều kiện ánh sáng."
              />
              <TechCard 
                icon={<CloudRain className="text-sky-400" />}
                title="GPM / TRMM Rainfall Data"
                content="Dữ liệu lượng mưa vệ tinh từ nhiệm vụ Global Precipitation Measurement, cung cấp cường độ mưa theo thời gian thực để phân tích tương quan mưa-ngập."
              />
              <TechCard 
                icon={<History className="text-purple-400" />}
                title="Dự báo AI (Gemini-3 Flash)"
                content="Mô hình ngôn ngữ lớn và thị giác máy tính kết hợp DEM (Mô hình độ cao số) để suy luận độ sâu ngập và đánh giá rủi ro kinh tế xã hội."
              />
            </div>
          </section>

          <section className="bg-slate-800/40 border border-slate-700 rounded-[2rem] p-8 backdrop-blur-sm">
            <h3 className="text-white font-bold text-lg mb-6 flex items-center gap-3">
              <HelpCircle className="w-5 h-5 text-amber-400" />
              Hướng dẫn giải đoán bản đồ
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <LegendItem color="bg-red-500" label="Vùng ngập sâu (>1.5m)" desc="Nguy hiểm cực độ, cần di dời khẩn cấp." />
              <LegendItem color="bg-orange-500" label="Vùng ngập trung bình (0.5 - 1.5m)" desc="Gây gián đoạn giao thông và sinh hoạt." />
              <LegendItem color="bg-blue-500" label="Vùng ngập nông (<0.5m)" desc="Ngập cục bộ tại các khu vực thấp trũng." />
              <LegendItem color="bg-slate-500" label="Ranh giới xã/huyện" desc="Đơn vị hành chính quản lý." />
            </div>
          </section>
        </div>

        {/* Right Column: Reporting Subscription */}
        <div className="space-y-8">
          <section className="bg-gradient-to-br from-blue-600/10 to-transparent border border-blue-500/20 rounded-[2rem] p-8 shadow-2xl relative overflow-hidden">
            <div className="absolute top-0 right-0 p-6 opacity-10">
              <Bell className="w-24 h-24 text-blue-400" />
            </div>
            
            <h3 className="text-white font-black text-xl mb-2 relative z-10">Báo cáo định kỳ</h3>
            <p className="text-slate-400 text-sm mb-8 relative z-10 font-medium">Đăng ký nhận báo cáo phân tích AI và bản đồ ngập lụt qua kênh liên lạc của bạn.</p>
            
            <form onSubmit={handleSubscribe} className="space-y-6 relative z-10">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Tần suất nhận tin</label>
                <div className="grid grid-cols-3 gap-2">
                  {['hourly', 'daily', 'weekly'].map((freq) => (
                    <button
                      key={freq}
                      type="button"
                      onClick={() => setFrequency(freq)}
                      className={`py-2 rounded-xl text-[10px] font-black uppercase transition-all ${
                        frequency === freq 
                        ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20' 
                        : 'bg-slate-900/50 text-slate-500 border border-slate-800'
                      }`}
                    >
                      {freq === 'hourly' ? 'Hàng giờ' : freq === 'daily' ? 'Hàng ngày' : 'Hàng tuần'}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Phương thức liên lạc</label>
                <div className="relative group">
                  <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                    <Mail className="h-4 w-4 text-slate-500 group-focus-within:text-blue-400 transition-colors" />
                  </div>
                  <input
                    type="text"
                    placeholder="Email hoặc Telegram ID..."
                    className="w-full bg-slate-950 border border-slate-800 text-white text-sm rounded-xl py-4 pl-12 pr-4 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                    value={contact}
                    onChange={(e) => setContact(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                className={`w-full py-4 rounded-xl font-black text-sm uppercase tracking-widest flex items-center justify-center gap-3 transition-all ${
                  subscribed 
                  ? 'bg-green-500 text-white' 
                  : 'bg-white text-slate-950 hover:bg-blue-400 hover:scale-[1.02]'
                }`}
              >
                {subscribed ? (
                  <>
                    <CheckCircle2 className="w-5 h-5" />
                    Đã đăng ký
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Kích hoạt thông báo
                  </>
                )}
              </button>
              
              {subscribed && (
                <p className="text-center text-[10px] text-green-400 font-bold animate-pulse">
                  Hệ thống đã xác nhận. Báo cáo tiếp theo sẽ gửi vào 08:00 AM.
                </p>
              )}
            </form>
          </section>

          <section className="bg-slate-800/40 border border-slate-700 rounded-[2rem] p-8 backdrop-blur-sm">
            <h3 className="text-white font-bold text-sm mb-4 flex items-center gap-2">
              <Settings className="w-4 h-4 text-slate-400" />
              Tùy chọn nâng cao
            </h3>
            <div className="space-y-4">
              <ToggleOption label="Cảnh báo khẩn cấp (>500mm mưa)" defaultChecked={true} />
              <ToggleOption label="Bản tóm tắt cho quản lý (AI)" defaultChecked={true} />
              <ToggleOption label="Dữ liệu Raw GeoJSON" defaultChecked={false} />
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

const TechCard = ({ icon, title, content }: { icon: React.ReactNode, title: string, content: string }) => (
  <div className="flex gap-5 p-6 bg-slate-900/40 rounded-3xl border border-slate-700/50 hover:bg-slate-800 transition-colors">
    <div className="w-12 h-12 bg-slate-950 rounded-2xl flex items-center justify-center shrink-0 border border-slate-800">
      {icon}
    </div>
    <div>
      <h4 className="text-white font-bold text-sm mb-1">{title}</h4>
      <p className="text-slate-400 text-xs leading-relaxed">{content}</p>
    </div>
  </div>
);

const LegendItem = ({ color, label, desc }: { color: string, label: string, desc: string }) => (
  <div className="p-4 bg-slate-900/30 rounded-2xl border border-slate-800 flex flex-col gap-2">
    <div className="flex items-center gap-3">
      <div className={`w-3 h-3 rounded-full ${color}`}></div>
      <span className="text-xs font-bold text-white uppercase">{label}</span>
    </div>
    <p className="text-[10px] text-slate-500 leading-tight">{desc}</p>
  </div>
);

const ToggleOption = ({ label, defaultChecked }: { label: string, defaultChecked: boolean }) => {
  const [enabled, setEnabled] = useState(defaultChecked);
  return (
    <div className="flex items-center justify-between p-3 bg-slate-900/30 rounded-xl border border-slate-800/50">
      <span className="text-[10px] font-semibold text-slate-300">{label}</span>
      <button 
        onClick={() => setEnabled(!enabled)}
        className={`w-8 h-4 rounded-full relative transition-colors ${enabled ? 'bg-blue-600' : 'bg-slate-700'}`}
      >
        <div className={`absolute top-0.5 w-3 h-3 bg-white rounded-full transition-all ${enabled ? 'right-0.5' : 'left-0.5'}`}></div>
      </button>
    </div>
  );
};
