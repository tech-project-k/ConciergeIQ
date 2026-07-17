import api from '../services/api';
import { Calendar, Compass, Phone, Globe, Mail, MapPin, Navigation, Car, AlertTriangle, ChevronDown, ChevronUp, CheckCircle, Ticket } from 'lucide-react';

export default function Timeline({ activities, warnings, tripId }) {
  const [selectedDay, setSelectedDay] = useState(1);
  const [expandedAct, setExpandedAct] = useState(null);
  const [bookingLoading, setBookingLoading] = useState(null);

  // Group activities by day
  const dayGroups = activities.reduce((groups, act) => {
    const d = act.day_number || 1;
    if (!groups[d]) groups[d] = [];
    groups[d].push(act);
    return groups;
  }, {});

  const days = Object.keys(dayGroups).map(Number).sort((a, b) => a - b);
  const currentActivities = dayGroups[selectedDay] || [];

  const toggleExpand = (id) => {
    setExpandedAct(expandedAct === id ? null : id);
  };

  const handleOpenClawBook = async (actId, e) => {
    e.stopPropagation();
    if (!tripId) {
      alert("Invalid trip context.");
      return;
    }
    setBookingLoading(actId);
    try {
      await api.post('/bookings', {
        trip_id: tripId,
        activity_id: actId
      });
      alert("OpenClaw secured your booking successfully!");
      window.location.reload();
    } catch (err) {
      console.error(err);
      alert("OpenClaw booking failed. Please verify reservation connection.");
    } finally {
      setBookingLoading(null);
    }
  };

  const getCategoryColor = (type) => {
    const lower = type.toLowerCase();
    if (lower.includes('hotel')) return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    if (lower.includes('breakfast') || lower.includes('lunch') || lower.includes('dinner')) return 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20';
    if (lower.includes('museum')) return 'bg-amber-500/10 text-amber-400 border-amber-500/20';
    if (lower.includes('coffee') || lower.includes('rest')) return 'bg-rose-500/10 text-rose-400 border-rose-500/20';
    return 'bg-violet-500/10 text-violet-400 border-violet-500/20';
  };

  return (
    <div className="space-y-6">
      {/* Dynamic Warnings */}
      {warnings && warnings.length > 0 && (
        <div className="p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 text-amber-300 text-xs space-y-2">
          <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-amber-400">
            <AlertTriangle className="w-4 h-4" />
            Concierge Alerts & Conflict Warnings
          </div>
          <ul className="list-disc list-inside space-y-1">
            {warnings.map((w, idx) => (
              <li key={idx} className="leading-relaxed">{w}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Day Selector Buttons */}
      {days.length > 0 && (
        <div className="flex gap-2 pb-2 border-b border-gray-900 overflow-x-auto">
          {days.map(d => (
            <button
              key={d}
              onClick={() => setSelectedDay(d)}
              className={`px-4.5 py-2.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all duration-200 ${
                selectedDay === d
                  ? 'bg-violet-600 text-white shadow-lg shadow-violet-500/10'
                  : 'bg-slate-900/60 text-gray-400 hover:text-white border border-slate-950'
              }`}
            >
              Day {d}
            </button>
          ))}
        </div>
      )}

      {/* Schedule Activities List */}
      <div className="space-y-4 relative pl-4 border-l border-slate-900">
        {currentActivities.length === 0 ? (
          <div className="text-gray-500 text-sm py-8 text-center">
            No activities scheduled for Day {selectedDay}.
          </div>
        ) : (
          currentActivities.map((act, idx) => {
            const isExpanded = expandedAct === act.id || expandedAct === idx;
            const prevAct = idx > 0 ? currentActivities[idx - 1] : null;
            
            return (
              <div key={act.id || idx} className="relative space-y-3">
                {/* Visual Timeline Marker Node */}
                <span className="absolute -left-[21px] top-4 w-2.5 h-2.5 rounded-full bg-violet-500 border border-slate-950 shadow shadow-violet-500/40" />

                {/* Transit Details Banner from previous point */}
                {idx > 0 && act.travel_distance_km > 0 && prevAct && (
                  <div className="flex items-center gap-2 text-[10px] text-gray-400 pl-4 py-1.5 bg-slate-950/70 border border-slate-900/60 rounded-xl w-full sm:w-fit leading-relaxed">
                    <Car className="w-3.5 h-3.5 text-violet-400 flex-shrink-0" />
                    <span>
                      {act.travel_mode === 'walking' ? '🚶 Walk' : '🚕 Ride'} &bull;{' '}
                      <strong>{act.travel_duration_min} mins</strong> ({act.travel_distance_km} km) from{' '}
                      <span className="text-gray-300 font-semibold">{prevAct.name}</span> to{' '}
                      <span className="text-gray-300 font-semibold">{act.name}</span>
                    </span>
                  </div>
                )}

                {/* Main Card */}
                <div
                  onClick={() => toggleExpand(act.id || idx)}
                  className="glass-panel rounded-2xl p-4 cursor-pointer hover:border-slate-800 transition flex flex-col justify-between"
                >
                  <div className="flex justify-between items-start gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-xs text-gray-500 font-bold bg-slate-950 px-2 py-0.5 rounded border border-slate-900">
                          {act.start_time} - {act.end_time}
                        </span>
                        <span className={`text-[10px] uppercase font-bold border px-2 py-0.5 rounded-full ${getCategoryColor(act.type)}`}>
                          {act.type}
                        </span>
                        {act.bookingConfirmationCode && (
                          <span className="inline-flex items-center gap-1 text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2.5 py-0.5 rounded-full font-bold">
                            <CheckCircle className="w-3 h-3" /> Secured
                          </span>
                        )}
                      </div>
                      <h4 className="text-sm md:text-base font-bold text-white mt-1">
                        {act.name}
                      </h4>
                      {act.description && (
                        <p className="text-xs text-gray-400 leading-relaxed mt-1">{act.description}</p>
                      )}
                    </div>
                    <div>
                      {isExpanded ? <ChevronUp className="w-5 h-5 text-gray-500" /> : <ChevronDown className="w-5 h-5 text-gray-500" />}
                    </div>
                  </div>

                  {/* Expanded Contact Info Details */}
                  {isExpanded && (
                    <div
                      className="mt-4 pt-4 border-t border-slate-900 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-gray-400 select-text cursor-default"
                      onClick={(e) => e.stopPropagation()} // Prevent card collapse on click
                    >
                      {act.address && (
                        <div className="flex items-start gap-2.5 sm:col-span-2">
                          <MapPin className="w-4 h-4 text-violet-400 flex-shrink-0 mt-0.5" />
                          <span>{act.address}</span>
                        </div>
                      )}
                      
                      {act.contact_phone && (
                        <div className="flex items-center gap-2.5">
                          <Phone className="w-4 h-4 text-violet-400 flex-shrink-0" />
                          <a href={`tel:${act.contact_phone}`} className="hover:text-violet-300 hover:underline">
                            {act.contact_phone}
                          </a>
                        </div>
                      )}

                      {act.contact_website && (
                        <div className="flex items-center gap-2.5">
                          <Globe className="w-4 h-4 text-violet-400 flex-shrink-0" />
                          <a href={act.contact_website} target="_blank" rel="noreferrer" className="hover:text-violet-300 hover:underline truncate">
                            {act.contact_website.replace("https://", "").replace("www.", "")}
                          </a>
                        </div>
                      )}

                      {act.cost > 0 && (
                        <div className="flex items-center gap-2.5 font-bold text-white bg-slate-950 px-3 py-1.5 rounded-lg border border-slate-900 w-fit">
                          <span>Est. Cost: ${act.cost}</span>
                        </div>
                      )}

                      {/* OpenClaw Booking Confirmation Details */}
                      {act.bookingConfirmationCode ? (
                        <div className="sm:col-span-2 p-3 bg-emerald-500/5 border border-emerald-500/10 rounded-xl text-emerald-400 text-xs font-medium space-y-1">
                          <div>Ticket secured via OpenClaw Booking API</div>
                          <div className="text-[10px] text-gray-500">Confirmation: <strong className="text-white select-all">{act.bookingConfirmationCode}</strong></div>
                        </div>
                      ) : (
                        ['event', 'lunch', 'dinner', 'museum'].includes(act.type.toLowerCase()) && (
                          <div className="sm:col-span-2">
                            <button
                              onClick={(e) => handleOpenClawBook(act.id, e)}
                              disabled={bookingLoading === act.id}
                              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-gradient-to-tr from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:from-violet-800 disabled:to-indigo-800 text-white font-bold transition shadow shadow-violet-500/5 flex items-center justify-center gap-2 text-xs cursor-pointer"
                            >
                              {bookingLoading === act.id ? (
                                <Loader className="w-4 h-4 animate-spin" />
                              ) : (
                                <>
                                  <Ticket className="w-4 h-4" /> Secure Ticket reservation (OpenClaw)
                                </>
                              )}
                            </button>
                          </div>
                        )
                      )}

                      {act.latitude && act.longitude && (
                        <div className="sm:col-span-2 pt-2 border-t border-slate-950 flex justify-end">
                          <a
                            href={`https://www.google.com/maps/search/?api=1&query=${act.latitude},${act.longitude}`}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-violet-600/10 hover:bg-violet-600/20 text-violet-400 border border-violet-500/15 rounded-lg transition font-semibold"
                          >
                            <Navigation className="w-3.5 h-3.5" /> Navigation Link
                          </a>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
