from typing import Dict, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.product import Product, ProductType
from app.schemas.validation import ValidationResponse, ValidationIssue


async def validate_configuration(
    components: Dict[str, str],
    db: AsyncSession,
) -> ValidationResponse:
    """
    Validate PC configuration compatibility.
    Checks: socket, RAM type/speed, PSU wattage, form factors.
    """
    issues: List[ValidationIssue] = []
    total_power = 0.0
    recommended_psu = 0.0
    
    # Fetch all component products
    product_ids = [UUID(pid) for pid in components.values() if pid]
    if not product_ids:
        return ValidationResponse(
            is_valid=False,
            issues=[ValidationIssue(
                component_type="general",
                issue_type="missing_components",
                severity="error",
                message="No components provided",
            )],
        )
    
    result = await db.execute(select(Product).where(Product.id.in_(product_ids)))
    products = {str(p.id): p for p in result.scalars().all()}
    
    # Get component mappings
    cpu_id = components.get("cpu")
    motherboard_id = components.get("motherboard")
    gpu_id = components.get("gpu")
    ram_id = components.get("ram")
    psu_id = components.get("psu")
    case_id = components.get("case")
    cooler_id = components.get("cooler")
    
    # 1. CPU-Motherboard socket compatibility
    if cpu_id and motherboard_id:
        cpu = products.get(cpu_id)
        mb = products.get(motherboard_id)
        
        if cpu and mb:
            cpu_socket = cpu.specifications.get("socket")
            mb_socket = mb.specifications.get("socket")
            
            if cpu_socket and mb_socket and cpu_socket != mb_socket:
                issues.append(ValidationIssue(
                    component_type="cpu",
                    issue_type="socket_mismatch",
                    severity="error",
                    message=f"CPU socket ({cpu_socket}) does not match motherboard socket ({mb_socket})",
                    details={"cpu_socket": cpu_socket, "mb_socket": mb_socket},
                ))
            
            # Check CPU power consumption
            cpu_tdp = cpu.specifications.get("tdp", 0)
            if isinstance(cpu_tdp, (int, float)):
                total_power += float(cpu_tdp)
    
    # 2. RAM compatibility
    if ram_id and motherboard_id:
        ram = products.get(ram_id)
        mb = products.get(motherboard_id)
        
        if ram and mb:
            ram_type = ram.specifications.get("type")  # DDR4, DDR5
            mb_ram_type = mb.specifications.get("ram_type")
            
            if ram_type and mb_ram_type and ram_type != mb_ram_type:
                issues.append(ValidationIssue(
                    component_type="ram",
                    issue_type="ram_type_mismatch",
                    severity="error",
                    message=f"RAM type ({ram_type}) does not match motherboard RAM type ({mb_ram_type})",
                    details={"ram_type": ram_type, "mb_ram_type": mb_ram_type},
                ))
            
            # Check RAM speed compatibility
            ram_speed = ram.specifications.get("speed")
            mb_max_speed = mb.specifications.get("ram_max_speed")
            if ram_speed and mb_max_speed:
                try:
                    if int(ram_speed) > int(mb_max_speed):
                        issues.append(ValidationIssue(
                            component_type="ram",
                            issue_type="ram_speed_warning",
                            severity="warning",
                            message=f"RAM speed ({ram_speed} MHz) exceeds motherboard max ({mb_max_speed} MHz)",
                        ))
                except (ValueError, TypeError):
                    pass
    
    # 3. GPU power consumption and form factor
    if gpu_id:
        gpu = products.get(gpu_id)
        if gpu:
            gpu_power = gpu.specifications.get("power_consumption", 0)
            if isinstance(gpu_power, (int, float)):
                total_power += float(gpu_power)
            
            # Check GPU dimensions vs case
            if case_id:
                case = products.get(case_id)
                if case:
                    gpu_length = gpu.specifications.get("length")
                    case_max_gpu = case.specifications.get("max_gpu_length")
                    
                    if gpu_length and case_max_gpu:
                        try:
                            if float(gpu_length) > float(case_max_gpu):
                                issues.append(ValidationIssue(
                                    component_type="gpu",
                                    issue_type="form_factor",
                                    severity="error",
                                    message=f"GPU length ({gpu_length} mm) exceeds case max ({case_max_gpu} mm)",
                                ))
                        except (ValueError, TypeError):
                            pass
    
    # 4. PSU wattage check
    if psu_id:
        psu = products.get(psu_id)
        if psu:
            psu_wattage = psu.specifications.get("wattage", 0)
            try:
                psu_wattage = float(psu_wattage)
                recommended_psu = total_power * 1.2  # 20% headroom
                
                if psu_wattage < total_power:
                    issues.append(ValidationIssue(
                        component_type="psu",
                        issue_type="insufficient_power",
                        severity="error",
                        message=f"PSU wattage ({psu_wattage}W) is insufficient. Required: ~{total_power:.0f}W",
                        details={"psu_wattage": psu_wattage, "required": total_power},
                    ))
                elif psu_wattage < recommended_psu:
                    issues.append(ValidationIssue(
                        component_type="psu",
                        issue_type="low_power_margin",
                        severity="warning",
                        message=f"PSU wattage ({psu_wattage}W) is close to recommended ({recommended_psu:.0f}W)",
                    ))
            except (ValueError, TypeError):
                pass
    
    # 5. Cooler compatibility
    if cooler_id and cpu_id:
        cooler = products.get(cooler_id)
        cpu = products.get(cpu_id)
        
        if cooler and cpu:
            cooler_sockets = cooler.specifications.get("socket", [])
            cpu_socket = cpu.specifications.get("socket")
            
            if cpu_socket and cooler_sockets:
                if isinstance(cooler_sockets, str):
                    cooler_sockets = [cooler_sockets]
                if cpu_socket not in cooler_sockets:
                    issues.append(ValidationIssue(
                        component_type="cooler",
                        issue_type="socket_mismatch",
                        severity="error",
                        message=f"Cooler does not support CPU socket ({cpu_socket})",
                    ))
            
            # Check cooler height vs case
            if case_id:
                case = products.get(case_id)
                if case:
                    cooler_height = cooler.specifications.get("height")
                    case_max_cooler = case.specifications.get("max_cooler_height")
                    
                    if cooler_height and case_max_cooler:
                        try:
                            if float(cooler_height) > float(case_max_cooler):
                                issues.append(ValidationIssue(
                                    component_type="cooler",
                                    issue_type="form_factor",
                                    severity="error",
                                    message=f"Cooler height ({cooler_height} mm) exceeds case max ({case_max_cooler} mm)",
                                ))
                        except (ValueError, TypeError):
                            pass
    
    is_valid = all(issue.severity != "error" for issue in issues)
    
    return ValidationResponse(
        is_valid=is_valid,
        issues=issues,
        total_power_consumption=total_power if total_power > 0 else None,
        recommended_psu_wattage=recommended_psu if recommended_psu > 0 else None,
    )

