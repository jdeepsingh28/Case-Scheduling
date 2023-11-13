def reformat_breadth_requirements(original_dict):
    breadth_section = "Computer Science Breadth Requirement"
    reformatted_breadth = []

    if breadth_section in original_dict:
        for breadth_area_dict in original_dict[breadth_section]:
            for breadth_area, details in breadth_area_dict.items():
                for course in details["courses"]:
                    reformatted_course = {
                        "breadth_area": breadth_area,
                        "requirement": details["requirement"],
                        "code": course["code"],
                        "name": course["name"],
                        "hours": course["hours"]
                    }
                    reformatted_breadth.append(reformatted_course)

    return reformatted_breadth