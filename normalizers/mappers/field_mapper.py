"""
Field mapper module for mapping fields between different data sources.
"""

from typing import Dict, Any, List, Optional, Callable


class FieldMapper:
    """
    Maps and transforms fields from different sources to a standardized format.
    
    Capabilities:
    - Field name mapping (rename)
    - Field value transformation
    - Nested field mapping
    - Conditional field mapping
    """
    
    def __init__(self):
        """Initialize field mapper."""
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self.transformers: Dict[str, Callable[[Any], Any]] = {}
    
    def register_mapping(
        self,
        source_name: str,
        field_map: Dict[str, str],
        transformers: Optional[Dict[str, Callable[[Any], Any]]] = None,
    ) -> None:
        """
        Register a field mapping for a source.
        
        Args:
            source_name: Name of the data source
            field_map: Mapping of source fields to target fields
            transformers: Optional field value transformers
        """
        self.mappings[source_name] = field_map
        
        if transformers:
            for field, transformer in transformers.items():
                self.transformers[f"{source_name}.{field}"] = transformer
    
    def map_entity(self, source_name: str, entity: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map entity fields from source format to standardized format.
        
        Args:
            source_name: Name of the data source
            entity: Entity data from source
            
        Returns:
            Mapped entity
        """
        if source_name not in self.mappings:
            return entity
        
        field_map = self.mappings[source_name]
        mapped = {}
        
        for source_field, target_field in field_map.items():
            if source_field in entity:
                value = entity[source_field]
                
                # Apply transformer if available
                transformer_key = f"{source_name}.{source_field}"
                if transformer_key in self.transformers:
                    value = self.transformers[transformer_key](value)
                
                mapped[target_field] = value
        
        # Include unmapped fields
        for key, value in entity.items():
            if key not in field_map and key not in mapped:
                mapped[key] = value
        
        return mapped
    
    def map_signal(self, source_name: str, signal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Map signal fields from source format to standardized format.
        
        Args:
            source_name: Name of the data source
            signal: Signal data from source
            
        Returns:
            Mapped signal
        """
        if source_name not in self.mappings:
            return signal
        
        mapped = signal.copy()
        
        # Map data field if present
        if "data" in mapped and isinstance(mapped["data"], dict):
            field_map = self.mappings[source_name]
            mapped_data = {}
            
            for source_field, target_field in field_map.items():
                if source_field in mapped["data"]:
                    value = mapped["data"][source_field]
                    
                    # Apply transformer
                    transformer_key = f"{source_name}.{source_field}"
                    if transformer_key in self.transformers:
                        value = self.transformers[transformer_key](value)
                    
                    mapped_data[target_field] = value
            
            mapped["data"] = mapped_data
        
        return mapped
    
    def map_batch(
        self, source_name: str, items: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Map a batch of items from source format.
        
        Args:
            source_name: Name of the data source
            items: List of items to map
            
        Returns:
            List of mapped items
        """
        return [self.map_entity(source_name, item) for item in items]
    
    def register_transformer(
        self, source_name: str, field: str, transformer: Callable[[Any], Any]
    ) -> None:
        """
        Register a field value transformer.
        
        Args:
            source_name: Name of the data source
            field: Field name
            transformer: Transformation function
        """
        key = f"{source_name}.{field}"
        self.transformers[key] = transformer
    
    def get_mappings(self) -> Dict[str, Dict[str, str]]:
        """Get all registered mappings."""
        return self.mappings.copy()
    
    def list_sources(self) -> List[str]:
        """List all registered sources."""
        return list(self.mappings.keys())
