import json
import os
import time
from typing import List, Dict, Optional
from src.pet_data import Pet, PetMemory, PetType, Direction, ChickenState

class SaveSystem:
    def __init__(self, save_directory: str = "pet_saves"):
        self.save_directory = save_directory
        self.save_file = os.path.join(save_directory, "pets_data.json")
        
        # Create save directory if it doesn't exist
        os.makedirs(save_directory, exist_ok=True)
    
    def save_pet(self, pet: Pet):
        """Save a single pet's data"""
        pets_data = self.load_all_pets_data()
        
        pet_data = {
            "memory": pet.memory.to_dict(),
            "position": pet.position,
            "direction": pet.direction.value,
            "current_state": pet.current_state.value,
            "last_save_time": time.time()
        }
        
        # Use pet name and type as unique identifier
        pet_id = f"{pet.memory.name}_{pet.memory.pet_type.value}"
        pets_data[pet_id] = pet_data
        
        self._write_save_file(pets_data)
    
    def save_all_pets(self, pets: List[Pet]):
        """Save all pets' data"""
        pets_data = {}
        
        for pet in pets:
            pet_data = {
                "memory": pet.memory.to_dict(),
                "position": pet.position,
                "direction": pet.direction.value,
                "current_state": pet.current_state.value,
                "last_save_time": time.time()
            }
            
            pet_id = f"{pet.memory.name}_{pet.memory.pet_type.value}"
            pets_data[pet_id] = pet_data
        
        self._write_save_file(pets_data)
    
    def load_all_pets_data(self) -> Dict:
        """Load all pets data from save file"""
        if not os.path.exists(self.save_file):
            return {}
        
        try:
            with open(self.save_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading save file: {e}")
            return {}
    
    def load_all_pets(self) -> List[Pet]:
        """Load all pets from save file"""
        pets_data = self.load_all_pets_data()
        pets = []
        
        for pet_id, pet_data in pets_data.items():
            try:
                pet = self._deserialize_pet(pet_data)
                if pet:
                    pets.append(pet)
            except Exception as e:
                print(f"Error loading pet {pet_id}: {e}")
                continue
        
        return pets
    
    def remove_pet(self, pet: Pet):
        """Remove a pet from save data"""
        pets_data = self.load_all_pets_data()
        pet_id = f"{pet.memory.name}_{pet.memory.pet_type.value}"
        
        if pet_id in pets_data:
            del pets_data[pet_id]
            self._write_save_file(pets_data)
    
    def pet_exists(self, name: str, pet_type: PetType) -> bool:
        """Check if a pet with given name and type already exists"""
        pets_data = self.load_all_pets_data()
        pet_id = f"{name}_{pet_type.value}"
        return pet_id in pets_data
    
    def _write_save_file(self, pets_data: Dict):
        """Write pets data to save file"""
        try:
            # Create backup of existing save file
            if os.path.exists(self.save_file):
                backup_file = self.save_file + ".backup"
                with open(self.save_file, 'r') as src:
                    with open(backup_file, 'w') as dst:
                        dst.write(src.read())
            
            # Write new save file
            with open(self.save_file, 'w') as f:
                json.dump(pets_data, f, indent=2)
                
        except IOError as e:
            print(f"Error saving pets data: {e}")
    
    def _deserialize_pet(self, pet_data: Dict) -> Optional[Pet]:
        """Deserialize pet data into Pet object"""
        try:
            # Load memory
            memory_data = pet_data["memory"]
            memory = PetMemory.from_dict(memory_data)
            
            # Create pet
            pet = Pet(
                memory=memory,
                position=tuple(pet_data.get("position", (100, 100))),
                direction=Direction(pet_data.get("direction", "down")),
                current_state=ChickenState(pet_data.get("current_state", "STAND")),
                target_position=None,  # Reset target position on load
                is_dragging=False  # Reset dragging state
            )
            
            # Update living time
            last_save_time = pet_data.get("last_save_time", time.time())
            time_offline = time.time() - last_save_time
            pet.memory.total_living_time += time_offline
            
            return pet
            
        except Exception as e:
            print(f"Error deserializing pet: {e}")
            return None
    
    def auto_save_pets(self, pets: List[Pet]):
        """Auto-save pets (called periodically)"""
        if pets:
            self.save_all_pets(pets)
    
    def get_save_file_path(self) -> str:
        """Get the path to the save file"""
        return self.save_file
    
    def backup_save_file(self) -> str:
        """Create a timestamped backup of the save file"""
        if not os.path.exists(self.save_file):
            return ""
        
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        backup_file = os.path.join(
            self.save_directory, 
            f"pets_data_backup_{timestamp}.json"
        )
        
        try:
            with open(self.save_file, 'r') as src:
                with open(backup_file, 'w') as dst:
                    dst.write(src.read())
            return backup_file
        except IOError as e:
            print(f"Error creating backup: {e}")
            return ""
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """Restore save data from a backup file"""
        if not os.path.exists(backup_file):
            return False
        
        try:
            with open(backup_file, 'r') as src:
                with open(self.save_file, 'w') as dst:
                    dst.write(src.read())
            return True
        except IOError as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def clear_all_saves(self):
        """Clear all save data (with confirmation needed by caller)"""
        try:
            if os.path.exists(self.save_file):
                os.remove(self.save_file)
            return True
        except IOError as e:
            print(f"Error clearing saves: {e}")
            return False