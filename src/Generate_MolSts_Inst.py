import string


# look in PairPotentials.h to get all the class names

dot_h_file = open("../include/rumd/PairPotential.h")
classNames = []
nextLine = dot_h_file.readline()
while nextLine:
    items = nextLine.split()
    # find lines which begin a new PairPotential class (but not the base class)
    if len(items) > 3 and items[0] == "class":
        clsName = items[1]
        baseName = items[4]
        if clsName.endswith(":"):
            clsName = clsName[:-1]
            baseName = items[3]
        if baseName.endswith("{"):
            baseName = baseName[:-1]
        # checking baseName is to avoid wrapper classes which change the interface a bit but do not have a different CalcF. However it is not guaranteed that this check is sufficient (for example if we derive from an existing PairPotential but still make a new CalcF)
        if clsName != "PairPotential" and baseName == "PairPotential":
            classNames.append(clsName)
    nextLine = dot_h_file.readline()

outfile = open("MolecularStress_Instantiation.inc","w")
outfile.write("""
///////////////////////////////////////////////////////////////////////////////
// This file has been generated by Generate_MolSts_Inst.py, do not edit!
///////////////////////////////////////////////////////////////////////////////
""")

for item in classNames:

    template_code = """
    %(class_name)s* pot_%(class_name)s = dynamic_cast<%(class_name)s*>(*potIter);
    if(pot_%(class_name)s) {
      int CM = pot_%(class_name)s->GetCutoffMethod();
      const float* d_params_loc = pot_%(class_name)s->GetDeviceParamsPtr();
      switch(CM) {

      """ % {"class_name":item}

    for cutoff_method in ["NS","SP","SF"]:
        template_code += """
        case(PairPotential::%(CM)s):
        if(test_LESB)
          mol_stress_tensor<PairPotential::%(CM)s><<<num_mol, threads_per_molecule, nbytes_shared>>>(pot_%(class_name)s, M->d_stress, particleData->d_r, M->d_vcm, M->d_cm, M->d_mlist, max_mol_size, num_mol, test_LESB, test_LESB->GetDevicePointer(), particleData->GetNumberOfTypes(), d_params_loc);
         else
           mol_stress_tensor<PairPotential::%(CM)s><<<num_mol, threads_per_molecule, nbytes_shared>>>(pot_%(class_name)s, M->d_stress, particleData->d_r, M->d_vcm, M->d_cm, M->d_mlist, max_mol_size, num_mol, test_RSB, test_RSB->GetDevicePointer(), particleData->GetNumberOfTypes(), d_params_loc);
        break;

    """ % {"CM":cutoff_method, "class_name":item}

    template_code += """
      } // end switch
    } // end if(pot_%(class_name)s)
  """ % {"class_name":item}


    outfile.write( template_code )
outfile.close()