#include <cctbx/boost_python/flex_fwd.h>

#include <boost/python/class.hpp>
#include <boost/python/args.hpp>
#include <iotbx/mtz/column.h>

namespace iotbx { namespace mtz {
namespace {

  struct object_wrappers
  {
    typedef object w_t;

    static void
    wrap()
    {
      using namespace boost::python;
      class_<w_t>("object", no_init)
        .def(init<>())
        .def(init<af::const_ref<int> const&>(
          (arg_("n_datasets_for_each_crystal"))))
        .def(init<const char*>((arg_("file_name"))))
        .def("title", &w_t::title)
        .def("history", &w_t::history)
        .def("space_group_name", &w_t::space_group_name)
        .def("point_group_name", &w_t::point_group_name)
        .def("space_group", &w_t::space_group)
        .def("n_batches", &w_t::n_batches)
        .def("n_reflections", &w_t::n_reflections)
        .def("space_group_number", &w_t::space_group_number)
        .def("max_min_resolution", &w_t::max_min_resolution)
        .def("n_crystals", &w_t::n_crystals)
        .def("n_active_crystals", &w_t::n_active_crystals)
        .def("crystals", &w_t::crystals)
        .def("lookup_column", &w_t::lookup_column, (arg_("label")))
      ;
    }
  };

  void
  wrap_all()
  {
    object_wrappers::wrap();
  }

} // namespace <anonymous>

namespace boost_python {

  void
  wrap_object() { wrap_all(); }

}}} // namespace iotbx::mtz::boost_python
