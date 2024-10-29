import { Button } from "@/components/ui/button"
import { FerrisWheel } from "lucide-react"
import { useNavigate } from "react-router-dom"

export default function Component() {
  const navigate = useNavigate();

  const handleStartSimulation = () => {
    navigate('/sim');
  };

  return (
    <div className="min-h-screen w-full bg-white flex items-center justify-center relative overflow-hidden">
      {/* Blurred background */}
      <div className="absolute inset-0 bg-white/80 backdrop-blur-md"></div>
      
      {/* Content container */}
      <div className="relative z-10 text-center space-y-8">
        <FerrisWheel className="w-24 h-24 mx-auto text-black animate-spin-slow" />
        <h1 className="text-4xl font-bold text-black">Welcome to the Game of Life</h1>
        <p className="text-lg text-gray-700 max-w-md mx-auto">
          Explore the fascinating world of cellular automata in this classic simulation.
        </p>
        <Button 
          className="bg-black text-white hover:bg-gray-800"
          onClick={handleStartSimulation}
        >
            Open Simulation
        </Button>
      </div>
      
      {/* Decorative elements */}
      <div className="absolute top-0 left-0 w-full h-16 bg-gradient-to-b from-black to-transparent opacity-10"></div>
      <div className="absolute bottom-0 left-0 w-full h-16 bg-gradient-to-t from-black to-transparent opacity-10"></div>
    </div>
  )
}
