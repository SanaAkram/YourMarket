print('# Super() functions ##########')

class Animal:
    def make_sound(self):
        print("Generic animal sound")


class Dog(Animal):
    def make_sound(self):
        super().make_sound()
        print("Bark! Bark!")


class Cat(Animal):
    def make_sound(self):
        super().make_sound()
        print("Meow!")


class DogCat(Dog, Cat):
    def make_sound(self):
        super().make_sound()
        print("DogCat says something confusing!")


# Creating an instance of DogCat
my_pet = DogCat()

# Calling the overridden method with super()
my_pet.make_sound()






print('# Aggregation ############')
class Professor:
    def __init__(self, name, employee_id):
        self.name = name
        self.employee_id = employee_id

class Department:
    def __init__(self, name, professors=[]):
        self.name = name
        self.professors = professors  # Aggregation: Department has Professors

    def add_professor(self, professor):
        self.professors.append(professor)

# Creating instances
professor1 = Professor("Dr. Smith", "EMP001")
professor2 = Professor("Dr. Johnson", "EMP002")

# Aggregation: Creating a Department with Professors
computer_science = Department("Computer Science", [professor1, professor2])

# Adding a new Professor to the Department
professor3 = Professor("Dr. Brown", "EMP003")
computer_science.add_professor(professor3)

# Accessing attributes
print(computer_science.name)          # Output: Computer Science
print(computer_science.professors)    # Output: [professor1, professor2, professor3]
